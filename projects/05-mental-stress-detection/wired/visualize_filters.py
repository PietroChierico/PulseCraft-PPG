# Copyright (c) 2026 Pietro Chierico
# SPDX-License-Identifier: MIT

"""
PPG Serial Reader - Real-Time Version with GUI Buttons

Window buttons:
- Raw Only
- Filtered Only
- Raw + Filtered
- Quit

Filter options:
0 = no filter
1 = real-time moving average
2 = real-time Butterworth bandpass filter
"""

import time
import re
from collections import deque

import serial
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from scipy.signal import butter, sosfilt, sosfilt_zi


# ===================== USER SETTINGS =====================

SERIAL_PORT = "COM3"
BAUDRATE = 115200

FS = 100.0  # Sampling frequency in Hz

FILTER_TYPE = 2
# 0 = no filter
# 1 = moving average
# 2 = Butterworth bandpass filter

MOVING_WINDOW = 15

LOWCUT = 0.5
HIGHCUT = 5.0
BUTTER_ORDER = 2

BUFFER_SIZE = 500

INITIAL_BUFFER_SECONDS = 5.0

PLOT_REALTIME = True
PLOT_EVERY_N_SAMPLES = 5

# Initial display mode:
# 1 = raw only
# 2 = filtered only
# 3 = raw + filtered
PLOT_MODE = 3

# =========================================================


running = True


def read_serial_value(serial_connection):
    """
    Read one numeric value from the serial port.

    The parser uses the last number in each line. This supports raw values,
    labeled values such as ``ir=90234``, and CSV formats such as
    ``time_us,ir`` or ``time_us,red,ir``.
    """
    line = serial_connection.readline().decode("utf-8", errors="ignore").strip()
    numbers = re.findall(r"[-+]?\d*\.?\d+", line)
    if not numbers:
        return None
    try:
        return float(numbers[-1])
    except ValueError:
        return None


class RealTimeMovingAverage:
    """
    Simple real-time moving average filter.
    """

    def __init__(self, window_size):
        self.buffer = deque(maxlen=window_size)

    def filter(self, value):
        self.buffer.append(value)
        return sum(self.buffer) / len(self.buffer)


class RealTimeButterworthBandpass:
    """
    Real-time Butterworth bandpass filter using SOS filtering.
    """

    def __init__(self, fs, lowcut, highcut, order):
        nyquist = 0.5 * fs
        low = lowcut / nyquist
        high = highcut / nyquist

        if low <= 0 or high >= 1 or low >= high:
            raise ValueError("Invalid bandpass filter frequencies.")

        self.sos = butter(
            order,
            [low, high],
            btype="bandpass",
            output="sos"
        )

        self.zi = sosfilt_zi(self.sos)
        self.initialized = False

    def filter(self, value):
        x = np.array([value])

        if not self.initialized:
            self.zi = self.zi * value
            self.initialized = True

        y, self.zi = sosfilt(self.sos, x, zi=self.zi)
        return y[0]


def create_filter():
    """
    Create the selected real-time filter.
    """
    if FILTER_TYPE == 0:
        return None

    if FILTER_TYPE == 1:
        return RealTimeMovingAverage(MOVING_WINDOW)

    if FILTER_TYPE == 2:
        return RealTimeButterworthBandpass(
            fs=FS,
            lowcut=LOWCUT,
            highcut=HIGHCUT,
            order=BUTTER_ORDER
        )

    raise ValueError("Invalid FILTER_TYPE selected.")


def set_plot_mode(mode):
    """
    Change the plot display mode.
    """
    global PLOT_MODE

    PLOT_MODE = mode

    if mode == 1:
        print("Display mode: raw signal only")
    elif mode == 2:
        print("Display mode: filtered signal only")
    elif mode == 3:
        print("Display mode: raw + filtered signals")


def stop_program(event=None):
    """
    Stop the acquisition loop.
    """
    global running
    running = False
    print("Stopping from window button...")


def setup_plot():
    """
    Create the real-time plot and GUI buttons.
    """
    plt.ion()

    fig, ax = plt.subplots()
    plt.subplots_adjust(bottom=0.22)

    raw_line, = ax.plot([], [], label="Raw PPG")
    filtered_line, = ax.plot([], [], label="Filtered PPG")

    ax.set_xlabel("Samples")
    ax.set_ylabel("PPG value")
    ax.set_title("Real-Time PPG Signal")
    ax.grid(True)
    ax.legend()

    # Button positions: [left, bottom, width, height]
    raw_button_ax = plt.axes([0.08, 0.05, 0.18, 0.075])
    filtered_button_ax = plt.axes([0.30, 0.05, 0.18, 0.075])
    both_button_ax = plt.axes([0.52, 0.05, 0.18, 0.075])
    quit_button_ax = plt.axes([0.74, 0.05, 0.18, 0.075])

    raw_button = Button(raw_button_ax, "Raw Only")
    filtered_button = Button(filtered_button_ax, "Filtered Only")
    both_button = Button(both_button_ax, "Raw + Filtered")
    quit_button = Button(quit_button_ax, "Quit")

    raw_button.on_clicked(lambda event: set_plot_mode(1))
    filtered_button.on_clicked(lambda event: set_plot_mode(2))
    both_button.on_clicked(lambda event: set_plot_mode(3))
    quit_button.on_clicked(stop_program)

    buttons = [raw_button, filtered_button, both_button, quit_button]

    return fig, ax, raw_line, filtered_line, buttons


def update_plot(fig, ax, raw_line, filtered_line, raw_buffer, filtered_buffer):
    """
    Update the real-time plot.
    """
    raw_data = np.array(raw_buffer)
    filtered_data = np.array(filtered_buffer)

    x = np.arange(len(raw_data))

    raw_line.set_data(x, raw_data)
    filtered_line.set_data(x, filtered_data)

    if PLOT_MODE == 1:
        raw_line.set_visible(True)
        filtered_line.set_visible(False)
        visible_data = raw_data

    elif PLOT_MODE == 2:
        raw_line.set_visible(False)
        filtered_line.set_visible(True)
        visible_data = filtered_data

    else:
        raw_line.set_visible(True)
        filtered_line.set_visible(True)
        visible_data = np.concatenate((raw_data, filtered_data))

    ax.set_xlim(0, BUFFER_SIZE)

    if len(visible_data) > 0:
        y_min = np.min(visible_data)
        y_max = np.max(visible_data)

        margin = 0.05 * (y_max - y_min + 1e-9)
        ax.set_ylim(y_min - margin, y_max + margin)

    ax.legend()

    fig.canvas.draw_idle()
    fig.canvas.flush_events()


def print_startup_info():
    """
    Print program settings.
    """
    print("=== PPG Real-Time Reader ===")
    print(f"Serial port: {SERIAL_PORT}")
    print(f"Baudrate: {BAUDRATE}")
    print(f"Sampling frequency: {FS} Hz")
    print(f"Filter type: {FILTER_TYPE}")
    print(f"Buffer size: {BUFFER_SIZE}")
    print(f"Initial buffer: {INITIAL_BUFFER_SECONDS} seconds")
    print("")
    print("Window buttons:")
    print("Raw Only")
    print("Filtered Only")
    print("Raw + Filtered")
    print("Quit")
    print("")


def main():
    global running

    raw_buffer = deque(maxlen=BUFFER_SIZE)
    filtered_buffer = deque(maxlen=BUFFER_SIZE)

    signal_filter = create_filter()

    initial_buffer_samples = int(INITIAL_BUFFER_SECONDS * FS)

    sample_count = 0
    running = True

    print_startup_info()

    serial_connection = None

    try:
        serial_connection = serial.Serial(
            SERIAL_PORT,
            BAUDRATE,
            timeout=1
        )

        time.sleep(2)

        if PLOT_REALTIME:
            fig, ax, raw_line, filtered_line, buttons = setup_plot()

        while running:
            value = read_serial_value(serial_connection)

            if value is None:
                continue

            sample_count += 1

            raw_buffer.append(value)

            if signal_filter is None:
                filtered_value = value
            else:
                filtered_value = signal_filter.filter(value)

            filtered_buffer.append(filtered_value)

            print(f"Raw: {value:.2f} | Filtered: {filtered_value:.2f}")

            if sample_count < initial_buffer_samples:
                continue

            if PLOT_REALTIME and sample_count % PLOT_EVERY_N_SAMPLES == 0:
                update_plot(
                    fig,
                    ax,
                    raw_line,
                    filtered_line,
                    raw_buffer,
                    filtered_buffer
                )

    except KeyboardInterrupt:
        print("\nStopping from keyboard interrupt...")

    except serial.SerialException as error:
        print(f"Serial error: {error}")

    finally:
        running = False

        if serial_connection is not None and serial_connection.is_open:
            serial_connection.close()
            print("Serial port closed")

        plt.ioff()
        plt.show()


if __name__ == "__main__":
    main()