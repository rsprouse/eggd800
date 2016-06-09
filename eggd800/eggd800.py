import hid
from collections import OrderedDict
import numpy as np
from ad7689 import Ad7689
from cs4245ctls import Cs4245Ctls
from gpiopins import GpioPins

class EggD800(object):
    '''Control of the Egg-D800 from Laryngograph.'''

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
        self.channel_sel = OrderedDict((
            ('audio', True),
            ('lx',    False),
            ('p2',    False),
            ('p1',    False),
            ('emg1',  False),
            ('emg2',  False),
            ('aux1',  False),
            ('aux2',  False)
        ))


    def select_channel(self, channel, selected=None):
        '''Select/deselect a channel by name.'''
        self.channel_sel[channel] = selected
        selections = []
        for idx, key in enumerate(self.channel_sel.keys()):
            if self.channel_sel[key] is True:
                selections.append(idx)
        self.ad7689.select_channels(selections)
        self.ad7689.set_output_report()

    def set_channel_mode(self, channel, mode):
        '''Set the channel mode, if applicable.'''
        if channel not in ('lx', 'p2'):
            msg = 'Unknown mode for channel "{:}".'.format(channel)
            raise RuntimeError(msg)
        if channel == 'lx':
            if mode not in ('gx', 'lx'):
                msg = 'Unknown mode "{:}" for channel "lx".'.format(mode)
                raise RuntimeError(msg)
            self.gpio.gx_sel = (mode == 'gx')
        if channel == 'p2':
            if mode not in ('nx', 'p2'):
                msg = 'Unknown mode "{:}" for channel "p2".'.format(mode)
                raise RuntimeError(msg)
            self.gpio.nx_pressure = (mode == 'nx')
        self.gpio.set_output_report()

#   Set variable gain on the specified control.
#   Input gain values are integers in the range
#   -24 to +24, corresponding to 0.5dB steps in the range -12.0dB to +12.0dB.
#   On the CS4245 the byte containing the gain values in the 0 to +12.0dB
#   range has decimal values 0 to 24 (0x00 to 0x24). The negative gain values
#   range from decimal 232 (-12.0dB) to 255 (-0.5dB) (0xe8 to 0xff).
#   Valid control names are "mic" and "lx".
#   When lxagc is True and control is 'lx', the lx automatic gain control is
#   turned on. It has no effect on the 'mic' control.
    def set_gain(self, control, val=12, lxagc=False):
        '''Set variable gain on audio/lx to val.'''
        val = np.int8(val)
        if val > 24 or val < -24:
            msg = 'Gain values must be between -24 and 24.'
            raise RuntimeError(msg)
        # For 8-bit integers casting from signed to unsigned causes 2^8 to be
        # added to negative values, which is what we need for the CS4245, e.g.
        # -24 signed corresponds to 232 unsigned, and -1 corresponds to 255.
        # Non-negative values as 0 to 24.
        val = np.uint8(np.int8(val))
        if control == 'mic':
            self.cs4245.mic_preamp = val
        elif control == 'lx':
            if lxagc is False:
                self.cs4245.lx_agc = 6
                self.cs4245.acc_preamp = val
            else:
                self.cs4245.lx_agc = 5
                self.cs4245.acc_preamp = 0
        self.cs4245.set_output_report()

