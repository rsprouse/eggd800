#!/usr/bin/env python

import os, sys
import numpy as np
import scipy.io.wavfile
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backend_tools import ToolBase
import matplotlib.ticker as ticker
import scipy.signal
import warnings
import sounddevice as sd
from eggd800.signal import butter_lowpass_filter
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QMessageBox

# Suppress annoying warning:
# UserWarning: Treat the new Tool classes introduced in v1.5 as experimental for now; the API and rcParam may change in future versions.
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    plt.rcParams['toolbar'] = 'toolmanager'
plt.rcParams['lines.linewidth'] = 0.5

class ConfirmationDlg(QWidget):
    '''A Yes/No confirmation dialog box.'''

    def __init__(self, *args, title='', msg='', question='', **kwargs):
        super(ConfirmationDlg, self).__init__(*args, **kwargs)
        self.title = title
        self.left = 100
        self.top = 100
        self.width = 320
        self.height = 200
        self.is_confirmed = None
        self.initUI(msg, question)
        
    def initUI(self, msg, question):
        global del_is_confirmed
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        r = QMessageBox.question(
            self,
            msg,
            question,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        self.is_confirmed = True if r == QMessageBox.Yes else False

class DelBtn(ToolBase):
    '''Delete Button for toolbar.'''
    def __init__(self, *args, acqfile, **kwargs):
        super(DelBtn, self).__init__(*args, **kwargs)
        self.acqfile = acqfile

    def trigger(self, sender, event, data):
        r = ConfirmationDlg(
            msg='Confirm deletion',
            question='Delete recording and exit?'
        )
        if r.is_confirmed is True:
            print(f'Deleting {self.acqfile}.')
            os.remove(self.acqfile)
            plt.close()

class Play(ToolBase):
    '''Play Button for toolbar.'''

    def __init__(self, *args, ax, audio, rate, **kwargs):
        super(Play, self).__init__(*args, **kwargs)
        self.ax = ax
        self.audio = audio
        self.rate = rate

    def trigger(self, sender, event, data):
        xmin, xmax = self.ax.get_xlim()
        xmin = int(xmin * self.rate) if xmin > 0 else 0
        xmax = int(xmax * self.rate) if xmax < len(self.audio) else len(self.audio)
        sd.stop()
        sd.play(self.audio[xmin:xmax], self.rate)

# From http://stackoverflow.com/questions/11086724/matplotlib-linked-x-axes-with-autoscaled-y-axes-on-zoom
def on_xlim_changed(ax):
    xlim = ax.get_xlim()
    for a in ax.figure.axes:
        # shortcuts: last avoids n**2 behavior when each axis fires event
        if a is ax or len(a.lines) == 0 or getattr(a, 'xlim', None) == xlim:
            continue

        ylim = np.inf, -np.inf
        for l in a.lines:
            x, y = l.get_data()
            # faster, but assumes that x is sorted
            start, stop = np.searchsorted(x, xlim)
            yc = y[max(start-1,0):(stop+1)]
            ylim = min(ylim[0], np.nanmin(yc)), max(ylim[1], np.nanmax(yc))

        # TODO: update limits from Patches, Texts, Collections, ...

        # x axis: emit=False avoids infinite loop
        a.set_xlim(xlim, emit=False)

        # y axis: set dataLim, make sure that autoscale in 'y' is on 
        corners = (xlim[0], ylim[0]), (xlim[1], ylim[1])
        a.dataLim.update_from_data_xy(corners, ignore=True, updatex=False)
        #a.autoscale(enable=True, axis='y')
        # cache xlim to mark 'a' as treated
        a.xlim = xlim

def egg_display(data, rate, chan, del_btn, title='', cutoff=50, order=3, acqfile=None):
    '''Make plot from multichannel data.'''
    chanmap = {c: idx for idx, c in enumerate(chan) if c is not None}
    ts = np.arange(data.shape[0]) / rate

    fig = plt.figure(figsize=(16,5))
    fig.canvas.manager.set_window_title(title)

    for plidx, (cname, cidx) in enumerate(chanmap.items()):
        spargs = {'sharex': fig.axes[0]} if len(fig.axes) > 0 else {}
        ax = fig.add_subplot(len(chanmap), 1, plidx+1, **spargs)
        cdata = data[:, cidx]
        if cname not in ('audio', 'lx'):
            cdata = butter_lowpass_filter(cdata, cutoff, rate, order)
        ax.plot(ts, cdata, scaley=False)
        ax.set_xlim((ts[0], ts[-1]))
        ax.set_ylim((data[:,cidx].min(), data[:,cidx].max()))
        ax.axhline(color='black')
        ax.set_title(cname)
        ax.callbacks.connect('xlim_changed', on_xlim_changed)
        ax.spines['top'].set_color('none')
        ax.spines['bottom'].set_color('none')
        ax.spines['left'].set_color('none')
        ax.spines['right'].set_color('none')
        ax.tick_params(
            axis='x',
            which='both',
            top=False,
            bottom=False,
            labelbottom=False
        )
    tm = fig.canvas.manager.toolmanager
    tm.add_tool(
        'play',
        Play,
        ax=fig.axes[0],
        audio=data[:,chanmap['audio']],
        rate=rate
    )
    fig.canvas.manager.toolbar.add_tool(tm.get_tool('play'), 'toolgroup1')
    if acqfile is not None:
        tm.add_tool('delete', DelBtn, acqfile=acqfile)
        fig.canvas.manager.toolbar.add_tool(tm.get_tool('delete'), 'toolgroup2')
    plt.show()
    return True

if __name__ == '__main__':
    wav = sys.argv[1]
    if wav == '--help':
        print("""
eggdisp.py - Display a multichannel EGG-D800 .wav file.

Usage:

eggdisp.py wavefile
eggdisp.py wavefile lowpass_cutoff
eggdisp.py wavefile lowpass_cutoff filter_order

The default lowpass cutoff is 50Hz, and the default filter order is 3.

""")
        exit(0)
    try:
        cutoff = float(sys.argv[2])
    except IndexError:
        cutoff = 50
    try:
        order = float(sys.argv[3])
    except IndexError:
        order = 3
    (rate, data) = scipy.io.wavfile.read(wav)
    egg_display(
        data,
        rate,
        ['audio', 'orfl', None, 'nsfl'],
        del_btn=None,
        title=wav,
        cutoff=cutoff,
        order=order,
        acqfile=wav
    )
