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
        {'id': 'tx', 'name': 'TX', 'desc': 'transmit data'},
        {'id': 'rx', 'name': 'RX', 'desc': 'receive data'}
    )
    
    options = (
        {'id': 'bitorder', 'desc': 'Bit order', 'default': 'msb-first', 'values': ('msb-first', 'lsb-first')},
        {'id': 'acc', 'desc': 'accuracy', 'default': 5},
    )
    annotations = (
        ('stp', 'Start pulse'),
        ('bit', 'Bit'),
        ('msgT', 'Message Transmit'),
        ('msgR', 'Message Receive'),
        ('par', 'Parity')
    )
    annotation_rows = (
        ('fields', 'Fields', (0, 1, 4)),
        ('msgval', 'Message trans', (2,)),
        ('msgrxval', 'Message receive', (3,))
    )

    # def __init__(self):
    #     self.reset()

    def reset(self):
        self.rise_sn = 0

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.sampleNum = []

#    def step(self, ss, direction):

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.stpTxAct = int(12.0 * (value/1000.0))
            self.stpTxPas = int(1.27 * (value/1000.0))
            self.oneBitTxAct = int(3.0 * (value/1000.0))
            self.oneBitTxPas = int(1.0 * (value/1000.0))
            self.zeroBitTxAct = int(1.0 * (value/1000.0))
            self.zeroBitTxPas = int(1.0 * (value/1000.0))
            self.endPulseTx = int(19.0 * (value/1000.0))
            self.stpRxAct = int(9.0 * (value/1000.0))
            self.stpRxPas = int(1.1 * (value/1000.0))
            self.oneBitRxAct = int(3.0 * (value/1000.0))
            self.oneBitRxPas = int(1.0 * (value/1000.0))
            self.zeroBitRxAct = int(1.0 * (value/1000.0))
            self.zeroBitRxPas = int(1.0 * (value/1000.0))
            self.endPulseRx = int(19.0 * (value/1000.0))
            self.TxRx = int(1.41 * (value/1000.0))
            self.RxTx = int(1.78 * (value/1000.0))
            

    def near(self,value,target):
        return True if ((value > (target - target*self.options['acc']/100)) and (value < (target + target*self.options['acc']/100))) else False

    def nowNear(self,target):
        samples = self.samplenum - self.sampleNum[-1]
        answer = True if ((samples > (target - target*self.options['acc']/100)) and (samples < (target + target*self.options['acc']/100))) else False
        self.sampleNum.append(self.samplenum)
        return answer

    def lastNear(self,target,time=1):
        time = abs(time)
        samples = self.sampleNum[-time] - self.sampleNum[-time-1]
        answer = True if ((samples > (target - target*self.options['acc']/100)) and (samples < (target + target*self.options['acc']/100))) else False
        return answer


    def decode(self):
        while True:
            pins = self.wait([{0:'r',1:'h'},{0:'l',1:'f'}])
            self.sampleNum.clear()
            self.sampleNum.append(self.samplenum)
            if pins[0] == 1:
                self.wait({0:'f'})
                if self.nowNear(self.stpTxAct):
                    self.wait({0:'r'})
                    if self.nowNear(self.stpTxPas):
                        self.put(self.sampleNum[-3], self.sampleNum[-1], self.out_ann, [0, ['Start pulse', 'Start']])
                        work = 1
                        i = 0
                        self.lsbMessage = 0
                        while work:
                            self.wait({0:'f'})
                            if self.nowNear(self.oneBitTxAct):
                                self.wait({0:'r'})
                                if self.nowNear(self.oneBitTxPas):
                                    if i != 10 and i!= 26:
                                        self.lsbMessage += 1 << i
                                        self.put(self.sampleNum[-3], self.sampleNum[-1], self.out_ann, [1, ['{0}'.format(i)]])
                                    else:
                                        self.put(self.sampleNum[-3], self.sampleNum[-1], self.out_ann, [4, ['{0}'.format(i)]])
                                    i += 1
                                else:
                                    self.put(self.sampleNum[0], self.samplenum, self.out_ann, [0, ['Error','Err']])
                                    break
                            elif self.lastNear(self.zeroBitTxAct):
                                self.wait({0:'r'})
                                if self.nowNear(self.zeroBitTxPas):
                                    self.put(self.sampleNum[-3], self.sampleNum[-1], self.out_ann, [1 if i != 10 and i!= 26 else 4, ['0']])
                                    i += 1
                                else:
                                    self.put(self.sampleNum[0], self.samplenum, self.out_ann, [0, ['Error','Err']])
                                    break
                            elif self.lastNear(self.endPulseTx):
                                self.put(self.sampleNum[-2], self.sampleNum[-1], self.out_ann, [0, ['End pulse','End']])
                                work = False
                            else:
                                self.put(self.sampleNum[0], self.sampleNum[-1], self.out_ann, [0, ['Error','Err']])
                                work = False
                                break
                        else:
                            self.msbMessage = 0
                            #i -= 1
                            for j in range(i):
                                self.msbMessage = self.msbMessage | ((( self.lsbMessage >> (39 - j) ) & 1 ) << j)
                            #even odd
                            #MSB LSB
                            #most significant byte
                            #least significant byte
                            self.even = (self.lsbMessage >> 10) & 1
                            self.odd = (self.lsbMessage >> 26) & 1
                            if self.even:
                                message = "even" 
                            elif self.odd:
                                message = "odd"
                            else:
                                message = ""
                            if self.options['bitorder'] == 'lsb-first':
                                message = message + " " + str(hex(self.lsbMessage))
                            else:
                                message = message + " " + str(hex(self.msbMessage))
                            self.put(self.sampleNum[0], self.sampleNum[-1], self.out_ann, [2, ['{0}'.format(message)]])
            else:
                self.wait({1:'r'})
                if self.nowNear(self.stpRxAct):
                    self.wait({1:'f'})
                    if self.nowNear(self.stpRxPas):
                        self.put(self.sampleNum[-3], self.sampleNum[-1], self.out_ann, [0, ['Start pulse', 'Start']])
                        work = 1
                        i = 0
                        self.lsbMessage = 0
                        while work:
                            self.wait({1:'r'})
                            if self.nowNear(self.oneBitRxAct):
                                self.wait({1:'f'})
                                if self.nowNear(self.oneBitRxPas):
                                    self.put(self.sampleNum[-3], self.sampleNum[-1], self.out_ann, [1, ['{0}'.format(i)]])
                                    self.lsbMessage += 1 << i
                                    i += 1
                                else:
                                    self.put(self.sampleNum[0], self.samplenum, self.out_ann, [3, ['Error','Err']])
                                    break
                            elif self.lastNear(self.zeroBitRxAct):
                                self.wait({1:'f'})
                                if self.nowNear(self.zeroBitRxPas):
                                    self.put(self.sampleNum[-3], self.sampleNum[-1], self.out_ann, [1, ['0']])
                                    i += 1
                                else:
                                    self.put(self.sampleNum[0], self.samplenum, self.out_ann, [3, ['Error','Err']])
                                    break
                            elif self.lastNear(self.endPulseRx):
                                self.put(self.sampleNum[-2], self.sampleNum[-1], self.out_ann, [0, ['End pulse','End']])
                                work = False
                            else:
                                self.put(self.sampleNum[0], self.samplenum, self.out_ann, [3, ['Error','Err']])
                                break
                        else:
                            self.msbMessage = 0
                            #i -= 1
                            for j in range(i):
                                self.msbMessage = self.msbMessage | ((( self.lsbMessage >> (39 - j) ) & 1 ) << j)
                            #even odd
                            #MSB LSB
                            #most significant byte
                            #least significant byte
                            if self.options['bitorder'] == 'lsb-first':
                                message = str(hex(self.lsbMessage))
                            else:
                                message = str(hex(self.msbMessage))
                            self.put(self.sampleNum[0], self.samplenum, self.out_ann, [3, ['{0}'.format(message)]])

