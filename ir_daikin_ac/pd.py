import sigrokdecode as srd
from .lists import *

class Decoder(srd.Decoder):
    api_version = 3        
    id = dev_id  
    name = dev_name        
    longname = dev_long
    desc = dev_desc
    license = 'gplv2+'
    inputs = ['logic']      
    outputs = []            
    tags = ['IR']
    channels = (            
        {'id': 'ir', 'name': 'IR', 'desc': 'Data line'},
    )
    options = (
        {'id': 'polarity', 'desc': 'Polarity', 'default': 'active-low',
            'values': ('active-low', 'active-high')},
        {'id': 'cd_freq', 'desc': 'Carrier Frequency', 'default': 0},
    )

    annotations = (
        ('bit', 'Bit'),                         #0
        ('agc-pulse', 'AGC pulse'),             #1
        ('longpause', 'Long pause'),            #2
        ('shortpause', 'Short pause'),          #3
        ('stop-bit', 'Stop bit'),               #4
        ('leader-code', 'Leader code'),         #5
        ('addr', 'Address'),                    #6
        ('addr-inv', 'Address#'),               #7
        ('mode', 'Mode'),                       #8
        ('count', 'Count'),                     #9
        ('frame', 'Frame'),                     #10
    )
    annotation_rows = (
        ('bits', 'Bits', (0, 1, 2, 3, 4,)),
        ('fields', 'Fields', (5, 6, 7, 10)),
        ('count', 'Count', (9,)),
        ('mode', 'Mode', (8,)),
    )
    
    def putx(self, data):
        self.put(self.ss_start, self.samplenum, self.out_ann, data)

    def putb(self, data):
        self.put(self.ss_bit, self.samplenum, self.out_ann, data)

    def putd(self, data):
        name = self.state.title()
        d = {'ADDRESS': 6, 'ADDRESS#': 7}
        self.putx([d[self.state], ['0x%02X' % (data),
                  '0x%02X' % (data),
                  '0x%02X' % (data), ]])      

    def putstop(self, ss):
        self.put(ss, ss + self.stop, self.out_ann,
                 [4, ['Stop bit', 'Stop', 'St', 'S']])

    def putframe(self, ss):
        self.put(ss, ss + self.daframe, self.out_ann,
                 [10, ['Frame bit', 'Frame', 'Fr', 'F']])

    def putpause(self, p):
        self.put(self.ss_start, self.ss_other_edge, self.out_ann,
                 [1, ['AGC pulse', 'AGC', 'A']])
        idx = 2 if p == 'Long' else 3
        self.put(self.ss_other_edge, self.samplenum, self.out_ann,
                 [idx, [p + ' pause', '%s-pause' % p[0], '%sP' % p[0], 'P']])

    def __init__(self):
        self.reset()

    def reset(self):
        self.state = 'IDLE'
        self.ss_bit = self.ss_start = self.ss_other_edge = self.ss_remote = 0
        self.data = self.count = self.active = None
        self.addr = self.cmd = None

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value
        self.tolerance = 0.20 # +/- 20%
        self.lc = int(self.samplerate * lc) - 1 # 5.15ms
        self.dazero = int(self.samplerate * zero) - 1 # 0.80ms
        self.daone = int(self.samplerate * one) - 1 # 1.763ms
        self.stop = int(self.samplerate * stop) - 1 # 0.50ms
        self.daframe = int(self.samplerate * frame) - 1 # 36.032ms

    def compare_with_tolerance(self, measured, base):
        return (measured >= base * (1 - self.tolerance)
                and measured <= base * (1 + self.tolerance))

    def handle_bit(self, tick):
        ret = None
        if self.compare_with_tolerance(tick, self.dazero):
            ret = 0
        elif self.compare_with_tolerance(tick, self.daone):
            ret = 1
        elif self.compare_with_tolerance(tick, self.daframe):
            ret = 2
        if ret in (0, 1):
            self.putb([0, ['%d' % ret]])
            self.data |= (ret << self.count) # LSB-first
            self.count = self.count + 1
        elif ret == 2:
            self.frame_bit()
        self.ss_bit = self.samplenum

    def frame_bit(self):
        self.putframe(self.ss_bit)
        self.ss_bit = self.ss_start = self.samplenum
        self.count = 0
        self.state = 'IDLE'

    def data_ok(self):
        if self.count == 8:
            self.putd(self.data)
            self.ss_start = self.samplenum
            return True
        self.putd(self.data >> 8)
        self.data = self.count = 0
        self.ss_bit = self.ss_start = self.samplenum

    def decode(self):
        cd_count = None
        if self.options['cd_freq']:
            cd_count = int(self.samplerate / self.options['cd_freq']) + 1
        prev_ir = None

        self.active = 0 if self.options['polarity'] == 'active-low' else 1
        statecount = 0

        while True:
            if cd_count:
                (cur_ir,) = self.wait([{0: 'e'}, {'skip': cd_count}])
                if self.matched[0]:
                    cur_ir = self.active
                if cur_ir == prev_ir:
                    continue
                prev_ir = cur_ir
                self.ir = cur_ir
            else:
                (self.ir,) = self.wait({0: 'e'})

            if self.ir != self.active:
                self.ss_other_edge = self.samplenum
                continue

            b = self.samplenum - self.ss_bit

            # State machine.
            if self.state == 'IDLE':
                if self.compare_with_tolerance(b, self.lc):
                    self.putpause('Long')
                    self.putx([5, ['Leader code', 'Leader', 'LC', 'L']])
                    self.ss_remote = self.ss_start
                    self.data = self.count = 0
                    self.state = 'ADDRESS'
                self.ss_bit = self.ss_start = self.samplenum

            elif self.state == 'ADDRESS':
                self.handle_bit(b)
                if self.count == 8:
                        self.state = 'ADDRESS#'
                        statecount += 1
                        for i in range(addrcount):
                            if statecount in header_addresses:
                                self.putx([8, [ ("Header") ]])
                            elif statecount in session_addresses:
                                self.putx([8, [ ("Session") ]])
                            elif statecount in state_address:
                                self.putx([8, [ ('States') ]])
                            elif statecount in temperature_address:
                                self.putx([8, [ ('Temp') ]])
                            elif statecount in fan_address:
                                self.putx([8, [ ('Fan') ]])
                            elif statecount in chsum_address:
                                self.putx([8, [ ('ChSum') ]])
                        self.putx([9, ['%d' % statecount]])
                        self.data_ok()
                if statecount == addrcount:
                    self.state = 'STOP'
                    statecount = 0

            elif self.state == 'ADDRESS#':
                self.handle_bit(b)
                if self.count == 16:
                        self.state = 'ADDRESS'
                        statecount += 1
                        for i in range(addrcount):
                            if statecount in header_addresses:
                                self.putx([8, [ ("Header") ]])
                            elif statecount in session_addresses:
                                self.putx([8, [ ("Session") ]])
                            elif statecount in state_address:
                                self.putx([8, [ ('States') ]])
                            elif statecount in temperature_address:
                                self.putx([8, [ ('Temperature') ]])
                            elif statecount in fan_address:
                                self.putx([8, [ ('Fan') ]])
                            elif statecount in chsum_address:
                                self.putx([8, [ ('CheckSum') ]])
                        self.putx([9, ['%d' % statecount]])
                        self.data_ok()
                if statecount == addrcount:
                    self.state = 'STOP'
                    statecount = 0

            elif self.state == 'FRAME':
                self.putstop(self.ss_bit)
                self.ss_bit = self.ss_start = self.samplenum
                self.state = 'IDLE'

            elif self.state == 'STOP':
                self.putstop(self.ss_bit)
                self.ss_bit = self.ss_start = self.samplenum
                self.state = 'IDLE'
           