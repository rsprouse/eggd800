import hid
from ad7689 import Ad7689
from cs4245ctls import Cs4245Ctls
from gpiopins import GpioPins

class EggD800(object):
    '''Control of the Egg-D800 from Laryngograph.'''

    @property
    def num_channels(self):
        return self.ad7689.num_channels

    @num_channels.setter
    def num_channels(self, val):
        self.ad7689.num_channels = val
        self.ad7689.set_output_report()

    @property
    def data_rate(self):
        return self.ad7689.data_rate

    @data_rate.setter
    def data_rate(self, val):
        self.ad7689.data_rate = val
        self.ad7689.set_output_report()

    def __init__(self, vendor_id=0x03eb, device_id=0x6801):
        self.vendor_id = vendor_id
        self.device_id = device_id
        h = hid.device()
        h.open(vendor_id, device_id)
        h.set_nonblocking(1)
        self.ad7689 = Ad7689(h)
        self.cs4245 = Cs4245Ctls(h)
        self.gpio = GpioPins(h)
        self.h = h
