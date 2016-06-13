import struct
from eggd800_hid import EggD800HID

class Ad7689(EggD800HID):
    '''Representation of AD7689 hardware in EGG-D800.'''
    
    @property
    def output_report(self):
        '''Output report based on current state of object attributes.'''
        rpt = bytearray(struct.pack(
            self.packed_fmt,
            self.report_num,
            self.num_channels,
            self.data_rate,
            *self.channels
        ))
        return rpt

    @property
    def data_rate(self):
        return self._data_rate

    @data_rate.setter
    def data_rate(self, val):
        if val in Ad7689._valid_rates:
            self._data_rate = val
        else:
            raise RuntimeError('Bad data rate {:}'.format(val))

    # These are the channels, as indicated by fourth through sixth bits:
    # e.g.     |||
    #   0b1010 000 100100100 (channel 0)
    #   0b1010 111 100100100 (channel 7)
    _channels = [
        0b1010000100100100,    # 0xa124 (IN0 0x2849<<2)
        0b1010001100100100,    # 0xa324 (IN1 0x28c9<<2)
        0b1010010100100100,    # 0xa524 (IN2 0x2949<<2)
        0b1010011100100100,    # 0xa724 (IN3 0x29c9<<2)
        0b1010100100100100,    # 0xa924 (IN4 0x2a49<<2)
        0b1010101100100100,    # 0xab24 (IN5 0x2ac9<<2)
        0b1010110100100100,    # 0xad24 (IN6 0x2b49<<2)
        0b1010111100100100     # 0xaf24 (IN7 0x2bc9<<2)
    ]
    # Allowed data rates.
    _valid_rates = (48000, 80000, 96000, 120000, 192000)
    
    def __init__(self, hid_handle):
        self.report_num = 1
        self.h = hid_handle
        self.num_channels = None
        self._data_rate = None
        self.packed_fmt = ''.join((
            '<',        # usb bus is little-endian
            'B',        # report number (1 byte)
            'I',        # number of channels (4 bytes)
            'I',        # total data rate (4 bytes)
            ('H' * 8)   # 8 channel settings (TODO: of what?) (2 bytes each)    
        ))
        self.packed_size = 1 + 4 + 4 + (2 * 8)
        self._set_from_handle()
        
    def _set_from_handle(self):
        '''Get object attributes from the HID handle.'''
        rpt = self.get_input_report()
        vals = struct.unpack(self.packed_fmt, bytearray(rpt))
        self.num_channels = vals[1]
        self.data_rate = vals[2]
        self.channels = list(vals[3:11])

    def select_channels(self, indexes):
        '''Set the selected channels based on list of indexes.'''
        for select_idx, channel_idx in enumerate(indexes):
            self.channels[select_idx] = Ad7689._channels[channel_idx]
        self.num_channels = len(indexes)
