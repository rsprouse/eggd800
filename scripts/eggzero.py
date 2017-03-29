#!/usr/bin/env python
# vim:fileencoding=utf-8

# Do a short acquisition to find DC offset for EGG-D800.

import pyaudio
import wave
import numpy as np
from eggd800.signal import demux

channels = 2
rate = 48000
bufflen = 1024
secs = 2

pa = pyaudio.PyAudio()
nchunks = int(rate / bufflen * secs)

s = pa.open(
    format=pyaudio.paInt16,
    channels=channels,
    rate=rate,
    input=True,
    frames_per_buffer=bufflen
)

frames = []
for idx in np.arange(0, nchunks):
    data = s.read(bufflen)
    frames.append(np.fromstring(data, dtype=np.int16))

npdata = np.hstack(frames)

s.stop_stream()
s.close()
pa.terminate()

# TODO: Verify that this decodes channels in the right way.
print(npdata.shape)
npdata = npdata.reshape([2, -1], order='F')
print(npdata.shape)
au, lx, p1, p2 = demux(npdata)

print(np.mean(au))
print(np.mean(lx))
print(np.mean(p1))
print(np.mean(p2))
