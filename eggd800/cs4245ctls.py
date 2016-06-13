import struct
from eggd800_hid import EggD800HID

class Cs4245Ctls(EggD800HID):
    '''Representation of the CS4245CTLS.'''
    ChipID     = 1
    PowerCtl   = 2
    DACCtl     = 3
    ADCCtl     = 4
    MCLKFreq   = 5
    AOutSel    = 6
    PGAChB     = 7
    PGAChA     = 8
    ADCIn      = 9
    DACChAVol  = 0x0A
    DACChBVol  = 0x0B
    DACCtl2    = 0x0C
    IRQStatus  = 0x0D
    IRQMask    = 0x0E
    IRQModeMSB = 0x0F
    IRQModeLSB = 0x10

    @property
    def output_report(self):
        '''Output report based on current state of object attributes.'''
        rpt = bytearray(struct.pack(
            self.packed_fmt,
            self.report_num,
            self.clock_freq,
            self.mic_preamp,
            self.acc_preamp,
            self.lx_agc,
            self.power_ctl,
            self.adc_ctl,
            self.aout_sel,
            self.dac_ctl,
            self.dac_ctl2,
            self.dac_cha_vol,
            self.dac_chb_vol,
            self.irq_status,
        ))
        return rpt

    def __init__(self, hid_handle):
        self.report_num = 3
        self.h = hid_handle
        # FIXME: packed_fmt cannot be used for both reading input reports and
        # writing output reports (report number seems to be used for the latter
        # but not the former)
        self.packed_fmt = ''.join((
            '<',        # usb bus is little-endian
            'B',        # report number (1 byte)
            'B',        # master clock frequency index [(48k default), 32k, 24k, 16k, 12k] (1 byte)
            'B',        # mic preamp gain (1 byte)
            'B',        # acc preamp
            'B',        # lx agc
            'B',        # PowerCtl
            'B',        # ADCCtl
            'B',        # AOutSel
            'B',        # DACCtl
            'B',        # DACCtl2
            'B',        # DACChAVol
            'B',        # DACChBVol
            'B'         # IRQStatus
        ))
        self.packed_size = 1 * 13
        self._set_from_handle()
        
    def _set_from_handle(self):
        '''Get object attributes from the HID handle.'''
        rpt = self.get_input_report()
        vals = struct.unpack(self.packed_fmt, bytearray(rpt))
        self.clock_freq = vals[1]
        self.mic_preamp = vals[2]
        self.acc_preamp = vals[3]
        self.lx_agc = vals[4]
        self.power_ctl = vals[5]
        self.adc_ctl = vals[6]
        self.aout_sel = vals[7]
        self.dac_ctl = vals[8]
        self.dac_ctl2 = vals[9]
        self.dac_cha_vol = vals[10]
        self.dac_chb_vol = vals[11]
        self.irq_status = vals[12]
