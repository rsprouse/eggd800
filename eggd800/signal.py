# Utility functions for working with EGG-D800 signals.

import scipy.signal

def demux(data, aero=True, audio_first=True):
    '''Separate a multiplexed EGG-D800 signal.
data = two-channel numpy array of multiplexed signal data
aero = demux aerodynamic signals if True (default=True)
audio_first = if True, first sample contains audio data; if False,
  the first sample contains aerodynamic data
  audio_first is ignored if the aero parameter is False
'''
    vals = []
    au_start = 0
    p_start = 1
    if audio_first is False and aero is True:
        au_start = 1
        p_start = 0
      
    if aero is True:
        au = data[au_start::2,0]
        lx = data[au_start::2,1]
        p2 = data[p_start::2,0]
        p1 = data[p_start::2,1]
        vals = [au, lx, p1, p2]
    else:
        au = data[0::2]
        lx = data[0::2]
        vals = [au, lx]
    return vals
 
def butter_lowpass(cut, fs, order=3):
    nyq = 0.5 * fs
    cut = cut / nyq
    b, a = scipy.signal.butter(order, cut, btype='low')
    return b, a

def butter_lowpass_filter(data, cut, fs, order=3):
    b, a = butter_lowpass(cut, fs, order=order)
    y = scipy.signal.filtfilt(b, a, data)
    return y

