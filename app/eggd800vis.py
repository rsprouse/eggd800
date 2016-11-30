#!/usr/bin/env python

import os, sys
import fnmatch
import numpy as np
import scipy.io.wavfile
import scipy.signal
import pyaudio
import runpy
from scipy import stats

from eggd800.signal import demux, butter_lowpass_filter

from bokeh.io import curdoc
from bokeh.layouts import row, column, widgetbox, gridplot
from bokeh.models import ColumnDataSource, CustomJS, Span, BoxAnnotation
from bokeh.models.tools import \
     CrosshairTool, BoxZoomTool, BoxSelectTool, HoverTool, \
     PanTool, ResetTool, SaveTool, TapTool, WheelZoomTool
from bokeh.models.widgets import Div, Slider, TextInput, PreText, Select, \
     Toggle, Button
from bokeh.plotting import figure, output_file, output_notebook, show
from bokeh.document import without_document_lock
from tornado import gen

def play_all():
    print('playing all')
    # create an audio object
    pya = pyaudio.PyAudio()

    # open stream based on the wave object which has been input.
    stream = pya.open(
                format = pyaudio.paInt16,
                channels = 1,
                rate = orig_rate,
                output = True)

    # read data (based on the chunk size)
    audata = au.astype(np.int16).to_string()
    stream.write(audata)

    # cleanup stuff.
    stream.close()    
    pya.terminate()

def get_filenames():
    '''Walk datadir and get all .wav filenamess.'''
    files = []
    for root, dirnames, fnames in os.walk(datadir):
        for fname in fnmatch.filter(fnames, '*.wav'):
            files.append(os.path.join(root, fname))
    return files

def load_calibration():
    '''Load calibration data and calculate calibration values.'''
# TODO: handle different calibration measurements, not just one for datadir
    global p1_cal, p2_cal
    try:
        # Load the variables in 'calibration.py'.
        calglobals = runpy.run_path(
            os.path.join(datadir, 'calibration.py')
        )

        # Store the calibration data and the linear regression.
        p1_cal = dict(data=calglobals['p1_data'])
        try:
            p1_zero_idx = p1_cal['data']['refinputs'].index(0.0)
            p1_offset = p1_cal['data']['measurements'][p1_zero_idx]
        except IndexError:
            p1_offset = 0.0
        p1_cal['regression'] = stats.linregress(
            np.array(p1_cal['data']['measurements']) - p1_offset,
            np.array(p1_cal['data']['refinputs'])
        )

        p2_cal = dict(data=calglobals['p2_data'])
        try:
            p2_zero_idx = p2_cal['data']['refinputs'].index(0.0)
            p2_offset = p2_cal['data']['measurements'][p2_zero_idx]
        except IndexError:
            p2_offset = 0.0
        p2_cal['regression'] = stats.linregress(
            np.array(p2_cal['data']['measurements']) - p2_offset,
            np.array(p2_cal['data']['refinputs'])
        )
    except Exception as e:
# TODO: print info/warning?
        print(e)
        p1_cal = None
        p2_cal = None
    print('p1_cal: ', p1_cal)
    print('p2_cal: ', p2_cal)

def calibrate(sig, slope=1.0, intercept=0.0, zero_offset=0.0):
    '''Calibrate a signal using slope, intercept, zero.'''
    return (sig - zero_offset - intercept) * slope

def load_file(attrname, old, wav):
    sys.stderr.write("++++++++++++++++++++++\n")
    global au, orig_au, lx, orig_lx, p1, orig_p1, p2, orig_p2, lp_p1, \
        orig_lp_p1, lp_p2, orig_lp_p2, rate, orig_rate, timepts, \
        raw_p1, raw_p2, raw_lp_p1, raw_lp_p2, raw_lp_decim_p1, raw_lp_decim_p2
    load_calibration()
    print(p1_cal)
    print(p2_cal)
    (orig_rate, data) = scipy.io.wavfile.read(os.path.join(datadir, wav))
    (orig_au, orig_lx, raw_p1, raw_p2) = demux(data)
    orig_rate /= 2            # effective sample rate is half the original rate (one quarter of the EGG-D800's total rate)
    raw_lp_p1 = butter_lowpass_filter(raw_p1, cutoff, orig_rate, order)
    raw_lp_p2 = butter_lowpass_filter(raw_p2, cutoff, orig_rate, order)
    if p1_cal is not None:
        try:
            zero_idx = p1_cal['data']['refinputs'].index(0.0)
            zero_offset = p1_cal['data']['measurements'][zero_idx]
        except IndexError:
            zero_offset = 0.0
        orig_p1 = calibrate(
            raw_lp_p1,
            p1_cal['regression'].slope,
            p1_cal['regression'].intercept,
            zero_offset
        )
    if p2_cal is not None:
        try:
            zero_idx = p2_cal['data']['refinputs'].index(0.0)
            zero_offset = p2_cal['data']['measurements'][zero_idx]
        except IndexError:
            zero_offset = 0.0
        orig_p2 = calibrate(
            raw_lp_p2,
            p2_cal['regression'].slope,
            p2_cal['regression'].intercept,
            zero_offset
        )
    orig_lp_p1 = butter_lowpass_filter(orig_p1, cutoff, orig_rate, order)
    orig_lp_p2 = butter_lowpass_filter(orig_p2, cutoff, orig_rate, order)
    decim_factor = 2
    au = scipy.signal.decimate(orig_au, decim_factor)
    lx = scipy.signal.decimate(orig_lx, decim_factor)
    p1 = scipy.signal.decimate(orig_p1, decim_factor)
    raw_lp_decim_p1 = scipy.signal.decimate(raw_lp_p1, decim_factor)
    p2 = scipy.signal.decimate(orig_p2, decim_factor)
    raw_lp_decim_p2 = scipy.signal.decimate(raw_lp_p2, decim_factor)
    rate = orig_rate / decim_factor  # rate also reduced by decim_factor
    print('done decimating')
    lp_p1 = butter_lowpass_filter(p1, cutoff, rate, order)
    lp_p2 = butter_lowpass_filter(p2, cutoff, rate, order)
    print('done filtering 2')
    sys.stderr.write("++++++++++++++++++++++\n")
    timepts = np.arange(0, len(au)) / rate
    step = np.int16(np.round(len(au) / width / 4))
    source.data['x'] = timepts[0::step]
    source.data['au'] = au[0::step]
    source.data['p1'] = lp_p1[0::step]
    source.data['raw_lp_decim_p1'] = raw_lp_p1[0::step]
    source.data['p2'] = lp_p2[0::step]
    source.data['raw_lp_decim_p2'] = raw_lp_p2[0::step]
    x_range.update(end=timepts[-1])
    sys.stderr.write("++++++++++++++++++++++\n")

def make_plot():
    '''Make the plot figures.'''
    ts = []
    ts.append(figure(
            width=width, height=height,
            title="Audio", y_axis_label=None,
            x_range=(0,30),
            tools=tools[0], webgl=True,
            tags=['audio_fig'],
            logo=None
        )
    )
    ts[0].line('x', 'au', source=source, tags=['update_ts'])
    ts[0].x_range.on_change('end', update_ts)
    ts[0].circle('x', 'au', source=source, size=0.1, tags=['update_ts'])
    cursel = BoxAnnotation(left=0, right=0, fill_alpha=0.1, fill_color='blue', tags=['cursel'])
    ts[0].add_layout(cursel)
    ts.append(figure(
            width=width, height=height,
            title="P1", y_axis_label='',
            x_range=ts[0].x_range,
            tools=tools[1], webgl=True,
            tags=['p1_fig'],
            logo=None
        )
    )
    ts[1].line('x', 'p1', source=source, tags=['update_ts'])
    ts[1].circle('x', 'p1', source=source, size=0.1, tags=['update_ts'])
    cursel = BoxAnnotation(left=0, right=0, fill_alpha=0.1, fill_color='blue', tags=['cursel'])
    ts[1].add_layout(cursel)
    ts.append(figure(
            width=width, height=height,
            title="P2", x_axis_label='seconds', y_axis_label='',
            x_range=ts[0].x_range,
            tools=tools[2], webgl=True,
            tags=['p2_fig'],
            logo=None
        )
    )
    ts[2].line('x', 'p2', source=source, tags=['update_ts'])
    ts[2].circle('x', 'p2', source=source, size=0.1, tags=['update_ts'])
    cursel = BoxAnnotation(left=0, right=0, fill_alpha=0.1, fill_color='blue', tags=['cursel'])
    ts[2].add_layout(cursel)
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
        newsource['raw_lp_decim_p1'] = raw_lp_decim_p1[0::step]
        newsource['p2'] = lp_p2[0::step]
        newsource['raw_lp_decim_p2'] = raw_lp_decim_p2[0::step]
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
        x1sel = np.min(ind) * step
        x2sel = np.max(ind) * step
        t1sel = x1sel / rate
        t2sel = x2sel / rate
        secs = t2sel - t1sel
        orig_x1sel = np.int(np.round((t1sel * orig_rate)))
        orig_x2sel = np.int(np.round((t2sel * orig_rate)))
        num_sel = orig_x2sel - orig_x1sel + 1
        p1_mean = np.mean(orig_lp_p1[orig_x1sel:orig_x2sel])
        p2_mean = np.mean(orig_lp_p2[orig_x1sel:orig_x2sel])
        if p1_cal is not None:
            p1m_lab = p1_cal['data']['refunits']
            p1s_lab = 'l'
        else:
            p1m_lab = 'raw'
            p1s_lab = 'raw'
        if p2_cal is not None:
            p2m_lab = p2_cal['data']['refunits']
            p2s_lab = 'l'
        else:
            p2m_lab = 'raw'
            p2s_lab = 'raw'
        msg = \
            'Time: {:0.2f}-{:0.2f} ({:0.2f})<br />'.format(
                t1sel, t2sel, secs
            ) + \
                'P1 mean: {:0.2f} {:}; sum: {:0.2f} {:}<br />'.format(
                p1_mean, p1m_lab, p1_mean * secs, p1s_lab
            ) + \
                'P2 mean: {:0.2f} {:}; sum: {:0.2f} {:}'.format(
                p2_mean, p2m_lab, p2_mean * secs, p2s_lab
        )
        msgdiv.text = msg
        for renderer in gp.select(dict(tags=['cursel'])):
            renderer.left = t1sel
            renderer.right = t2sel
    else:
        msgdiv.text = ''

# Filename selector
datadir = os.path.join(os.path.dirname(__file__), 'data')
fsel = Select(options=['Select a file'] + get_filenames(), width=600)

msgdiv = Div(text='', width=400, height=50)

step = None
rate = orig_rate = None
au = orig_au = lx = orig_lx = p1 = orig_p1 = p2 = orig_p2 = []
lp_p1 = orig_lp_p1 = lp_p2 = orig_lp_p2 = timepts = []
raw_p1 = raw_p2 = raw_lp_p1 = raw_lp_p2 = raw_lp_decim_p1 = raw_lp_decim_p2 = []
p1_cal = p2_cal = None
width = 800
height = 200
cutoff = 50
order = 3
source = ColumnDataSource(
    data=dict(
        x=timepts,
        au=au,
        p1=p1,
        raw_lp_decim_p1=p1,
        p2=p2,
        raw_lp_decim_p2=p2
    )
)

# Create the tools for the toolbar
ts_cnt = np.arange(3)
cross = [CrosshairTool() for n in ts_cnt]
hover = [
    HoverTool(tooltips=[('time', '$x'), ('sample', '@x')]),
    HoverTool(tooltips=[('time', '$x'), ('val', '@p1'), ('raw', '@raw_lp_decim_p1')]),
    HoverTool(tooltips=[('time', '$x'), ('val', '@p2'), ('raw', '@raw_lp_decim_p2')])
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

play_all_button = Button(label='All', button_type='success', width=60)
play_all_button.on_click(play_all)

fsel.on_change('value', load_file)
source.on_change('selected', selection_change)

curdoc().add_root(row(fsel, play_all_button, msgdiv))
(gp, ch0) = make_plot()
x_range = ch0.x_range
curdoc().add_root(row(gp))
