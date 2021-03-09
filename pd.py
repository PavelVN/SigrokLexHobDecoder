##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2015 Petteri Aimonen <jpa@sigrok.mail.kapsi.fi>
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, see <http://www.gnu.org/licenses/>.
##

import sigrokdecode as srd

class Decoder(srd.Decoder):
    api_version = 3
    id = 'pvn_lex_hob'
    name = 'Lex hob decoder'
    longname = 'Lex hob decoder'
    desc = 'Decoder for signal of Lex hob'
    license = 'mit'
    inputs = ['logic']
    outputs = ['empty']
    tags = ['Embedded/industrial']
    channels = (
        {'id': 'rx', 'name': 'RX', 'desc': 'receive data'},
    )
    
    options = (
        {'id': 'dir', 'desc': 'direction', 'default': 'rx',
         'values': ('rx', 'tx')},
    )
    annotations = (
        ('stp', 'Start pulse'),
        ('bit', 'Bit'),
        ('msg', 'Message'),
    )
    annotation_rows = (
        ('fields', 'Fields', (0, 1)),
        ('msgval', 'Message row', (2,))
    )

    # def __init__(self):
    #     self.reset()

    def reset(self):
        self.rise_sn = 0

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

#    def step(self, ss, direction):

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.stpNumMin = int(11.5 * (value/1000.0))
            self.stpNumMax = int(12.5 * (value/1000.0))
            self.oneBitNumMin = int(2.7 * (value/1000.0))
            self.oneBitNumMax = int(3.3 * (value/1000.0))
            self.zeroBitNumMin = int(0.9 * (value/1000.0))
            self.zeroBitNumMax = int(1.1 * (value/1000.0))
            self.endNumMin = int(18.5 * (value/1000.0))
            self.endNumMax = int(19.5 * (value/1000.0))


    def decode(self):
        while True:
            self.wait({0:'r'})
            self.first_rise_samplenum = self.samplenum
            self.wait({0:'f'})
            if self.samplenum - self.first_rise_samplenum > self.stpNumMin and self.samplenum - self.first_rise_samplenum < self.stpNumMax:
                self.put(self.first_rise_samplenum, self.samplenum, self.out_ann, [0, ['Start pulse', 'Start']])
                work = 1
                i = 0
                self.message = 0
                while work:
                    self.wait({0:'r'})
                    self.rise_samplenum = self.samplenum
                    self.wait({0:'f'})
                    if self.samplenum - self.rise_samplenum > self.oneBitNumMin and self.samplenum - self.rise_samplenum < self.oneBitNumMax:
                        self.put(self.rise_samplenum, self.samplenum, self.out_ann, [1, ['{0}'.format(i)]])
                        self.message += 1 << i
                        i += 1
                    elif self.samplenum - self.rise_samplenum > self.zeroBitNumMin and self.samplenum - self.rise_samplenum < self.zeroBitNumMax:
                        self.put(self.rise_samplenum, self.samplenum, self.out_ann, [1, ['0']])
                        i += 1
                    elif self.samplenum - self.rise_samplenum > self.endNumMin and self.samplenum - self.rise_samplenum < self.endNumMax:
                        self.put(self.rise_samplenum, self.samplenum, self.out_ann, [0, ['End pulse','End']])
                        work = False
                    else:
                        self.put(self.rise_samplenum, self.samplenum, self.out_ann, [0, ['Error','Err']])
                else:
                    self.messageInv = 0
                    #i -= 1
                    for j in range(i):
                        self.messageInv = self.messageInv | ((( self.message >> (39 - j) ) & 1 ) << j)
                    #even odd
                    #MSB LSB
                    #most significant byte
                    #least significant byte
                    self.even = (self.message >> 10) & 1
                    self.odd = (self.message >> 26) & 1
                    self.put(self.first_rise_samplenum, self.samplenum, self.out_ann, [2, ['{0} {1} {2} {3}'.format(self.even, self.odd, hex(self.message), hex(self.messageInv))]])

