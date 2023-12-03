import argparse
import queue
import sys
import numpy as np
import sounddevice as sd
import keyboard
import os
import time
last_clap_time = time.time()
file_path = r"C:\Users\artur\OneDrive\Töölaud\Portfolio\projekt_2\Projekt-2\mingi.pptx"  # Replace with your file path
os.startfile(file_path)
def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument(
    '-l', '--list-devices', action='store_true',
    help='show list of audio devices and exit')
args, remaining = parser.parse_known_args()
if args.list_devices:
    print(sd.query_devices())
    parser.exit(0)
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[parser])
parser.add_argument(
    'channels', type=int, default=[1], nargs='*', metavar='CHANNEL',
    help='input channels to plot (default: the first)')
parser.add_argument(
    '-d', '--device', type=int_or_str,
    help='input device (numeric ID or substring)')
parser.add_argument(
    '-r', '--samplerate', type=float, help='sampling rate of audio device')
parser.add_argument(
    '-n', '--downsample', type=int, default=10, metavar='N',
    help='display every Nth sample (default: %(default)s)')
args = parser.parse_args(remaining)
if any(c < 1 for c in args.channels):
    parser.error('argument CHANNEL: must be >= 1')
mapping = [c - 1 for c in args.channels]  # Channel numbers start with 1
q = queue.Queue()

# Constants for clap detection
CLAP_THRESHOLD = 0.54  # Adjust this threshold as needed
CLAP_SAMPLES = int(0.05 * args.samplerate) if args.samplerate else 441  # Adjust the window size as needed

def detect_clap(signal):
    """Detects a clap based on amplitude threshold."""
    global last_clap_time  # Declare the variable as global to modify it within this function

    if max(signal) > CLAP_THRESHOLD:
        current_time = time.time()
        # Check if enough time has passed since the last clap detection
        if current_time - last_clap_time > 1.0:  # Adjust the duration (1.0 seconds) as needed
            last_clap_time = current_time  # Update the last clap time
            return True
    return False

def audio_callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    q.put(indata[::args.downsample, mapping])

try:
    if args.samplerate is None:
        device_info = sd.query_devices(args.device, 'input')
        args.samplerate = device_info['default_samplerate']

    stream = sd.InputStream(
        device=args.device, channels=max(args.channels),
        samplerate=args.samplerate, callback=audio_callback)
    
    with stream:
        while True:
            try:
                data = q.get_nowait()
                if detect_clap(data):
                    print("Clap detected!")  # Print when a clap is detected
                    keyboard.press_and_release('right')
                
            except queue.Empty:
                pass
except Exception as e:
    parser.exit(type(e).__name__ + ': ' + str(e))
