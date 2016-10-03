#!/usr/bin/env python

import os, sys
import numpy as np
import scipy.io.wavfile
import scipy.signal
import pyaudio

from eggd800.signal import demux, butter_lowpass_filter

from bokeh.io import curdoc
from bokeh.layouts import row, column, widgetbox, gridplot
from bokeh.models import ColumnDataSource, CustomJS
from bokeh.models.tools import \
     CrosshairTool, BoxZoomTool, BoxSelectTool, HoverTool, \
     PanTool, ResetTool, SaveTool, TapTool, WheelZoomTool
from bokeh.models.widgets import Div, Slider, TextInput, PreText, Select, Button
from bokeh.plotting import figure, output_file, output_notebook, show
from bokeh.document import without_document_lock
from tornado import gen

def play_all():
    print('playing all')
    # create an audio object
    pya = pyaudio.PyAudio()

    # open stream based on the wave object which has been input.
    stream = pya.open(
                format = pyaudio.paINT16,
                channels = 1,
                rate = rate,
                output = True)

    # read data (based on the chunk size)
    audata = au.astype(np.INT16).to_string()
    stream.write(audata)

    # cleanup stuff.
    stream.close()    
    pya.terminate()

def get_filenames():
    '''Get all the .wav files in the current working dir.'''
    files = [name for name in os.listdir(datadir) if name.endswith('.wav')]
    return files

def load_file(attrname, old, wav):
    sys.stderr.write("++++++++++++++++++++++\n")
    global au, lx, p1, p2, lp_p1, lp_p2, rate, timepts
    (rate, data) = scipy.io.wavfile.read(os.path.join(datadir, wav))
    decim_factor = 2
    (au, lx, p1, p2) = demux(data)
    au = scipy.signal.decimate(au, decim_factor)
    lx = scipy.signal.decimate(lx, decim_factor)
    p1 = scipy.signal.decimate(p1, decim_factor)
    p2 = scipy.signal.decimate(p2, decim_factor)
    #p1 = (p1 - 196.0) / 14.0   # phony calibration in cc/s
    #p2 = (p2 - 786.0) * 0.00122 # phony calibration in cmH2O
    lp_p1 = butter_lowpass_filter(p1, cutoff, rate, order)
    lp_p2 = butter_lowpass_filter(p2, cutoff, rate, order)
    rate /= 2            # effective sample rate is half the original rate (one quarter of the EGG-D800's total rate)
    rate /= decim_factor  # rate also reduced by decim_factor
    timepts = np.arange(0, len(au)) / rate
    step = np.int16(np.round(len(au) / width / 4))
    source.data['x'] = timepts[0::step]
    source.data['au'] = au[0::step]
    source.data['p1'] = lp_p1[0::step]
    source.data['p2'] = lp_p2[0::step]
    x_range.update(end=timepts[-1])

def make_plot():
    '''Make the plot figures.'''
    ts = []
    ts.append(figure(
            width=width, height=height,
            title="Audio", y_axis_label=None,
            x_range=(0,30),
            tools=tools[0], webgl=True
        )
    )
    ts[0].line('x', 'au', source=source, tags=['update_ts'])
    ts[0].x_range.on_change('end', update_ts)
    ts[0].circle('x', 'au', source=source, size=0.1, tags=['update_ts'])
    ts.append(figure(
            width=width, height=height,
            title="Oral airflow", y_axis_label='ml/s',
            x_range=ts[0].x_range,
            tools=tools[1], webgl=True
        )
    )
    ts[1].line('x', 'p1', source=source, tags=['update_ts'])
    ts[1].circle('x', 'p1', source=source, size=0.1, tags=['update_ts'])
    ts.append(figure(
            width=width, height=height,
            title="Oral pressure", x_axis_label='seconds', y_axis_label='cmH2O',
            x_range=ts[0].x_range,
            tools=tools[2], webgl=True
        )
    )
    ts[2].line('x', 'p2', source=source, tags=['update_ts'])
    ts[2].circle('x', 'p2', source=source, size=0.1, tags=['update_ts'])
    gp = gridplot([[ts[0]], [ts[1]], [ts[2]]])
    return (gp, ts[0])

@gen.coroutine
def update_ts_with_lock():
    global data_update_in_progress
    sys.stderr.write("with_lock\n")

@gen.coroutine
@without_document_lock
def update_ts_wrap():
    sys.stderr.write("wrapper\n")
    global data_update_in_progress
    curdoc().add_next_tick_callback(update_ts_with_lock)
    yield gen.sleep(1)
    data_update_in_progress = False
    
def update_data(start, end):
    global step
    dur = end - start
    if dur <= 2.0:
        newstep = 1
    elif dur <= 5.0:
        newstep = np.int16(np.round(len(au) / width / 8))
    elif dur <= 10.0:
        newstep = np.int16(np.round(len(au) / width / 4))
    else:
        newstep = np.int16(np.round(len(au) / width / 2))
    if newstep != step:
        sys.stderr.write('Updating source data\n')
        step = newstep
        newsource = dict()
        newsource['x'] = timepts[0::step]
        newsource['au'] = au[0::step]
        newsource['p1'] = lp_p1[0::step]
        newsource['p2'] = lp_p2[0::step]
        source.data = newsource
        for renderer in ch0.select(dict(tag='update_ts')):
            renderer.data_source.data = newsource
        # TODO: should this trigger fire?
        #source.trigger('change')
    else:
        sys.stderr.write('Step did not change\n')
    print(dur, step, len(au), width)
    
#@gen.coroutine
def update_ts(attr, old, new):
    sys.stderr.write("*****update_ts_start***********\n")
    global data_update_in_progress
    if not data_update_in_progress:
        print(attr)
        print(old)
        print(new)
        print(x_range.start, x_range.end)
        data_update_in_progress = True
        update_data(x_range.start, x_range.end)
#        curdoc().add_next_tick_callback(update_ts_wrap)
        data_update_in_progress = False
    else:
        data_update_in_progress = False
        sys.stderr.write("--data update in progress--------------\n")
    sys.stderr.write("*****update_ts_end***********\n")

def selection_change(attr, old, new):
    sys.stderr.write("*****selection_change***********\n")
    ind = new['1d']['indices']
    if len(ind) > 1:
        start = np.min(ind)
        end = np.max(ind)
        msg = \
            'Time: {:0.2f}-{:0.2f} ({:0.2f})<br />'.format(
                start / rate,
                end / rate,
                (end - start) / rate
            ) + \
                'P1 mean: {:0.2f} sum: {:0.2f}<br />'.format(
                np.mean(lp_p1[start:end]),
                np.sum(lp_p1[start:end])
            ) + \
                'P2 mean: {:0.2f} sum: {:0.2f}'.format(
            np.mean(lp_p2[start:end]),
            np.sum(lp_p2[start:end])
        )
        msgdiv.text = msg
    else:
        msgdiv.text = ''

# Filename selector
datadir = os.path.join(os.path.dirname(__file__), 'data')
fsel = Select(options=['Select a file'] + get_filenames())

msgdiv = Div(text='', width=400, height=50)

step = None
rate = None
au = lx = p1 = p2 = lp_p1 = lp_p2 = timepts = []
width = 800
height = 200
cutoff = 50
order = 3
source = ColumnDataSource(
    data=dict(
        x=timepts,
        au=au,
        p1=p1,
        p2=p2
    )
)

# Create the tools for the toolbar
ts_cnt = np.arange(3)
cross = [CrosshairTool() for n in ts_cnt]
hover = [
    HoverTool(tooltips=[('time', '$x'), ('sample', '@x')]),
    HoverTool(tooltips=[('time', '$x'), ('val', '@p1')]),
    HoverTool(tooltips=[('time', '$x'), ('val', '@p2')])
]
xzoom = [BoxZoomTool(dimensions=['width']) for n in ts_cnt]
xwzoom = [WheelZoomTool(dimensions=['width']) for n in ts_cnt]
xsel = [BoxSelectTool(dimensions=['width']) for n in ts_cnt]
xtsel = [TapTool() for n in ts_cnt]
xpan = [PanTool(dimensions=['width']) for n in ts_cnt]
save = [SaveTool() for n in ts_cnt]
reset = [ResetTool() for n in ts_cnt]
tools = [
    [
        cross[n], hover[n], xpan[n], xzoom[n], xwzoom[n],
        xsel[n], xtsel[n], save[n], reset[n]
    ]
    for n in ts_cnt
]

data_update_in_progress = False

fsel.on_change('value', load_file)
source.on_change('selected', selection_change)

curdoc().add_root(row(fsel, msgdiv))
(gp, ch0) = make_plot()
x_range = ch0.x_range
curdoc().add_root(row(gp))

