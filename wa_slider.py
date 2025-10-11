#
# wa_slider.py
# Waveform Alignment Slider
#
# Steven J. Gibbons
# 2025/10/11
#
# Reads in SAC files for two different events at a station
# and allows the user to slide the signal from one event over the signal
# from the reference event.
# User specifies 3 different traces
# The user clicks a time to output a line to a file.
#
# If we specify station STATION and events EV1 and EV2
# then the program expects to find directories
#
# topdir/STATION.EV1
# and
# topdir/STATION.EV2
#
# If we specify the channels STATION.COMP1 STATION.COMP2 STATION.COMP3
# then it expects to find all of 
#  STATION.COMP1.sac STATION.COMP2.sac STATION.COMP3.sac
# in BOTH directories.
# The user will have to modify the code if variants of this are required.
#
import sys
import argparse
import os
import matplotlib.pyplot as plt
from obspy import read, UTCDateTime
from obspy.signal.filter import bandpass
from matplotlib.widgets import Slider
import numpy as np

#
scriptname = sys.argv[0]
numarg     = len(sys.argv) - 1
text       = 'Specify '
text      += '--f1 [freq1] '
text      += '--f2 [freq2] '
text      += '--ccval [ccval] '
text      += '--outfile       [outfile] '
text      += '--ev1 [event1] '
text      += '--ev2 [event2] '
text      += '--station [station] '
text      += '--chan1 [chan1name] '
text      += '--chan2 [chan2name] '
text      += '--chan3 [chan3name] '
text      += '--phase [phase] '
text      += '--topdir [topdir] '
parser     = argparse.ArgumentParser( description = text )
parser.add_argument("--f1", help="Frequency 1", default=None, required=True )
parser.add_argument("--f2", help="Frequency 2", default=None, required=True )
parser.add_argument("--ccval", help="ccval", default=1.0, required=False )
parser.add_argument("--ev1", help="Event 1", default=None, required=True )
parser.add_argument("--ev2", help="Event 2", default=None, required=True )
parser.add_argument("--station", help="Station", default=None, required=True )
parser.add_argument("--outfile", help="output file", default='relative_times.txt', required=False )
parser.add_argument("--chan1", help="chan1name", default=None, required=False )
parser.add_argument("--chan2", help="chan2name", default=None, required=False )
parser.add_argument("--chan3", help="chan3name", default=None, required=False )
parser.add_argument("--phase", help="phase", default='P', required=False )
parser.add_argument("--topdir", help="topdir", default='.', required=False )

args = parser.parse_args()

f1            = float( args.f1 )
f2            = float( args.f2 )
ccval         = float( args.ccval )
ev1           = args.ev1
ev2           = args.ev2
station       = args.station
outfile       = args.outfile
chan1         = args.chan1
chan2         = args.chan2
chan3         = args.chan3
phase         = args.phase
topdir        = args.topdir

# Frequency arguments for bandpass filter
#f1 = 1.0  # Lower frequency
#f2 = 4.0  # Upper frequency

# Directories containing SAC files for two events
# dir_event1 = "AAK.DPRK4"
# dir_event2 = "AAK.DPRK3"
dir_event1 = topdir + "/" + station + "." + ev1
dir_event2 = topdir + "/" + station + "." + ev2

# Read SAC files for each component from both events
# components = ["BHE", "BHN", "BHZ"]
components = [ chan3, chan2, chan1 ]
traces_event1 = {comp: read(os.path.join(dir_event1, f"{comp}.sac"))[0] for comp in components}
traces_event2 = {comp: read(os.path.join(dir_event2, f"{comp}.sac"))[0] for comp in components}

# Apply bandpass filter and normalize each trace
for comp in components:
    tr1 = traces_event1[comp]
    tr2 = traces_event2[comp]
    tr1.data = bandpass(tr1.data, f1, f2, tr1.stats.sampling_rate, corners=4, zerophase=True)
    tr2.data = bandpass(tr2.data, f1, f2, tr2.stats.sampling_rate, corners=4, zerophase=True)
    npts = len(tr1.data)
    start = int(npts * 0.3)
    end = int(npts * 0.7)

    tr1.data /= np.max(np.abs(tr1.data[start:end]))
    tr2.data /= np.max(np.abs(tr2.data[start:end]))
# Resample both traces to 2000 Hz
    tr1.resample(2000)
    tr2.resample(2000)

# Plotting function with slider for time shifting and click capture
def interactive_alignment():
    ##NOTy fig, axs = plt.subplots(len(components), 1, figsize=(10, 8), sharex=True, sharey=True)
    fig, axs = plt.subplots(len(components), 1, figsize=(10, 8), sharex=True )
    plt.subplots_adjust(bottom=0.25)

    lines_event1 = []
    lines_event2 = []
    clicked_time = [None]  # Use list to allow modification in nested function

    for i, comp in enumerate(components):
        t1 = traces_event1[comp].times()
        t2 = traces_event2[comp].times()
        data1 = traces_event1[comp].data
        data2 = traces_event2[comp].data

        npts = len(t1)
        start = int(npts * 0.3)
        end = int(npts * 0.7)

        line1, = axs[i].plot(t1[start:end], data1[start:end], label=ev1)
        line2, = axs[i].plot(t2[start:end], data2[start:end], label=ev2)
        axs[i].set_title(comp)
        axs[i].set_ylim(-1.1, 1.1)
        axs[i].legend()

        lines_event1.append(line1)
        lines_event2.append(line2)

    ax_slider = plt.axes([0.2, 0.1, 0.65, 0.03])
    slider = Slider(ax_slider, 'Time Shift (s)', -10.0, 10.0, valinit=0.0)

    def update(val):
        shift = slider.val
        for i, comp in enumerate(components):
            t2 = traces_event2[comp].times()
            t2_shifted = t2[start:end] + shift
            lines_event2[i].set_xdata(t2_shifted)
            # Preserve current axis limits
            xlim = axs[i].get_xlim()
            ylim = axs[i].get_ylim()
            # Restore axis limits to preserve zoom
            axs[i].set_xlim(xlim)
            axs[i].set_ylim(ylim)
        fig.canvas.draw_idle()

    def onclick(event):
        if event.inaxes in axs:
            clicked_time[0] = event.xdata
            print(f"Clicked time on reference trace: {clicked_time[0]} seconds")

    fig.canvas.mpl_connect('button_press_event', onclick)
    slider.on_changed(update)
    plt.show()

    return slider.val, clicked_time[0]

# Run the interactive alignment tool
final_shift, clicked_time = interactive_alignment()

# Output the final time difference
print(f"Final time difference between the two events: {final_shift} seconds")

if clicked_time is not None:
    ref_start_time = traces_event1[chan1].stats.starttime
    shifted_start_time = traces_event2[chan1].stats.starttime

    ref_epoch = ref_start_time + clicked_time
    shifted_epoch = shifted_start_time + clicked_time + final_shift

    print(" --- Time Information ---")
    print(f"Reference trace clicked time (epoch): {ref_epoch.timestamp}")
    print(f"Reference trace clicked time (ISO): {ref_epoch.isoformat()}")
    print(f"Shifted trace corresponding time (epoch): {shifted_epoch.timestamp}")
    print(f"Shifted trace corresponding time (ISO): {shifted_epoch.isoformat()}")
    timediff      = shifted_epoch.timestamp - ref_epoch.timestamp
    line  =         ev1
    line += "   " + ev2
    line += "   " + ref_epoch.isoformat()
    line += "   " + shifted_epoch.isoformat()
    line += "   " + station
    line += "   " + phase
    line += "   " + "{:.4f}".format( ccval ).rjust(9)  + " "
    line += "   " + "{:.4f}".format( timediff ).rjust(20)  + "\n"
    print (line)
    f = open( outfile, "a" )
    f.write( line )
    f.close()
else:
    print("No time was clicked on the reference trace.")
