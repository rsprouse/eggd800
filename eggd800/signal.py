# Utility functinos for working with EGG-D800 signals.

import scipy.signal

def demux(data, aero=True):
    '''Separate a multiplexed EGG-D800 signal.
data = two-channel numpy array of multiplexed signal data
aero = demux aerodynamic signals if True (default=True)
'''
    vals = []
    if aero is True:
        au = data[0::2,0]
        lx = data[0::2,1]
        p2 = data[1::2,0]
        p1 = data[1::2,1]
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
    y = scipy.signal.lfilter(b, a, data)
    return y

