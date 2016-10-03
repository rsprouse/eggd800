
def demux(signal, aero=True):
    '''Separate a multiplexed EGG-D800 signal.
signal = two-channel numpy array of multiplexed signal data
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
 
