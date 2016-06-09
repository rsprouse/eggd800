import struct
from eggd800_hid import EggD800HID

class GpioPins(EggD800HID):
    '''Representation of the GPIO pins.'''
    LOWMICPREAMP   = 0x00000001L  # 00000000000000000000000000000001
    GXSEL          = 0x00000002L  # 00000000000000000000000000000010
    FASTAGC        = 0x00000004L  # 00000000000000000000000000000100
    NXPRESSURE     = 0x00000008L  # 00000000000000000000000000001000
    ACCPREAMP      = 0x00000010L  # 00000000000000000000000000010000
    VINSEL         = 0x00000020L  # 00000000000000000000000000100000
    I2CPRESSURE    = 0x00000040L  # 00000000000000000000000001000000
    P3CONNECTOR    = 0x000FC000L  # 00000000000011111100000000000000
    MANOMETRY      = 0x00F00000L  # 00000000111100000000000000000000
    AD7689CHANNELS = 0xFF000000L  # 11111111000000000000000000000000

    @property
    def bitmask(self):
# TODO: gx_sel seems to work opposite to how it is intended
# TODO: check nx_pressure
# TODO: check preamp
        if self.gx_sel is True:
            self._bitmask |= GpioPins.GXSEL
        else:
            self._bitmask &= ~GpioPins.GXSEL
        if self.nx_pressure is True:
            self._bitmask |= GpioPins.NXPRESSURE
        else:
            self._bitmask &= ~GpioPins.NXPRESSURE
        if self._low_mic_preamp:
            self._bitmask |= GpioPins.LOWMICPREAMP
        else:
            self._bitmask &= ~GpioPins.LOWMICPREAMP
        return self._bitmask

    @bitmask.setter
    def bitmask(self, val):
        '''The bitmask attribute can be assigned as a single unit.'''
        self._bitmask = val

    @property
    def output_report(self):
        '''Output report based on current state of object attributes.'''
        rpt = bytearray(struct.pack(
            self.packed_fmt,
            self.report_num,
            self.bitmask
        ))
        return rpt

    def __init__(self, hid_handle):
        self.report_num = 4
        self.h = hid_handle
        # FIXME: packed_fmt cannot be used for both reading input reports and
        # writing output reports (report number seems to be used for the latter
        # but not the former)
        self.packed_fmt = ''.join((
            '<',        # usb bus is little-endian
            'B',        # report number (1 byte)
            'I',        # bitmask (4 bytes)
        ))
        self.packed_size = 1 + 4
        self.gx_sel = None
        self.nx_pressure = None
        self._low_mic_preamp = None
        self._set_from_handle()
        
    def _set_from_handle(self):
        '''Get object attributes from the HID handle.'''
        rpt = self.get_input_report()
        # FIXME: don't hardcode format (and array indexes?)
        vals = struct.unpack('<I', bytearray(rpt[0:4]))
        self.bitmask = vals[0]
        if self.bitmask & GpioPins.GXSEL:
            self.gx_sel = True  # TODO: use a meaningful value
        else:
            self.gx_sel = False
        if self.bitmask & GpioPins.NXPRESSURE:
            self.nx_pressure = True 
        else:
            self.nx_pressure = False
        if self.bitmask & GpioPins.LOWMICPREAMP:
            self._low_mic_preamp = 1
        else:
            self._low_mic_preamp = 0
