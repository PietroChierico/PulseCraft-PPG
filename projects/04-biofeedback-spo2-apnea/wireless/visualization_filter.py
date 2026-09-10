# Copyright (c) 2026 Pietro Chierico
# SPDX-License-Identifier: MIT

"""
PPG WiFi Infrared Reader - Real-Time Version with GUI Buttons

Expected WiFi TCP input:
Each received line must contain Red and Infrared numeric values:

Example formats:
Red: 12345 Infrared: 67890
Red: 12345 IR: 67890
12345, 67890
12345 67890
1000, 12345, 67890

The program ignores Red and visualizes only Infrared. For three-column streams such as millis,red,ir, the last value is used as Infrared.

Window buttons:
- Raw IR Only
- Filtered IR Only
- Raw + Filtered IR
- Quit

Filter options:
0 = no filter
1 = real-time moving average
2 = real-time Butterworth bandpass filter
"""

import time
from collections import deque

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from scipy.signal import butter, sosfilt, sosfilt_zi

from ppg_wifi_ir_stream import WiFiPPGClient, parse_ir_value


# ===================== USER SETTINGS =====================

ESP32_HOST = "192.168.4.1"
TCP_PORT = 3333
TCP_CONNECT_TIMEOUT_S = 5.0
TCP_LINES_PER_READ = 50

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
# 1 = raw infrared only
# 2 = filtered infrared only
# 3 = raw + filtered infrared
PLOT_MODE = 3

# =========================================================


running = True


def parse_infrared_value(line):
    """
    Extract only the infrared value from one WiFi TCP line.

    Red is intentionally ignored in this visualizer. The shared parser supports
    labeled streams, Red/IR pairs, and millis,red,ir streams.
    """
    return parse_ir_value(line)


def read_wifi_infrared_values(wifi_client):
    """
    Read infrared values from the WiFi TCP stream.

    Returns an empty list when no complete TCP lines are currently available.
    """
    infrared_values = []

    for line in wifi_client.read_lines(TCP_LINES_PER_READ):
        infrared_value = parse_infrared_value(line)

        if infrared_value is not None:
            infrared_values.append(infrared_value)

    return infrared_values


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
        print("Display mode: raw infrared signal only")
    elif mode == 2:
        print("Display mode: filtered infrared signal only")
    elif mode == 3:
        print("Display mode: raw + filtered infrared signals")


def stop_program(event=None):
    """
    Stop the acquisition loop.
    """
    global running
    running = False
    print("Stopping program...")


def setup_plot():
    """
    Create the real-time plot and GUI buttons.
    """
    plt.ion()

    fig, ax = plt.subplots()
    plt.subplots_adjust(bottom=0.22)

    raw_line, = ax.plot([], [], label="Raw Infrared")
    filtered_line, = ax.plot([], [], label="Filtered Infrared")

    ax.set_xlabel("Samples")
    ax.set_ylabel("Infrared PPG value")
    ax.set_title("Real-Time WiFi Infrared PPG Signal")
    ax.grid(True)
    ax.legend()

    fig.canvas.mpl_connect("close_event", stop_program)

    # Button positions: [left, bottom, width, height]
    raw_button_ax = plt.axes([0.08, 0.05, 0.18, 0.075])
    filtered_button_ax = plt.axes([0.30, 0.05, 0.18, 0.075])
    both_button_ax = plt.axes([0.52, 0.05, 0.18, 0.075])
    quit_button_ax = plt.axes([0.74, 0.05, 0.18, 0.075])

    raw_button = Button(raw_button_ax, "Raw IR Only")
    filtered_button = Button(filtered_button_ax, "Filtered IR Only")
    both_button = Button(both_button_ax, "Raw + Filtered")
    quit_button = Button(quit_button_ax, "Quit")

    raw_button.on_clicked(lambda event: set_plot_mode(1))
    filtered_button.on_clicked(lambda event: set_plot_mode(2))
    both_button.on_clicked(lambda event: set_plot_mode(3))

    def quit_from_button(event):
        stop_program(event)
        plt.close(fig)

    quit_button.on_clicked(quit_from_button)

    # Keep button references alive
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

    fig.canvas.draw_idle()
    fig.canvas.flush_events()


def print_startup_info():
    """
    Print program settings.
    """
    print("=== PPG WiFi Infrared Real-Time Reader ===")
    print(f"ESP32 host: {ESP32_HOST}")
    print(f"TCP port: {TCP_PORT}")
    print(f"TCP connect timeout: {TCP_CONNECT_TIMEOUT_S} seconds")
    print(f"TCP lines per read: {TCP_LINES_PER_READ}")
    print(f"Sampling frequency: {FS} Hz")
    print(f"Filter type: {FILTER_TYPE}")
    print(f"Buffer size: {BUFFER_SIZE}")
    print(f"Initial buffer: {INITIAL_BUFFER_SECONDS} seconds")
    print("")
    print("WiFi TCP input format:")
    print("Each line must contain Red and Infrared values")
    print("Red is ignored; only Infrared is visualized and filtered")
    print("")
    print("Window buttons:")
    print("Raw IR Only")
    print("Filtered IR Only")
    print("Raw + Filtered")
    print("Quit")
    print("")


def main():
    global running

    raw_infrared_buffer = deque(maxlen=BUFFER_SIZE)
    filtered_infrared_buffer = deque(maxlen=BUFFER_SIZE)

    signal_filter = create_filter()

    initial_buffer_samples = int(INITIAL_BUFFER_SECONDS * FS)

    sample_count = 0
    running = True

    print_startup_info()

    wifi_client = None
    fig = None

    try:
        wifi_client = WiFiPPGClient(
            ESP32_HOST,
            TCP_PORT,
            connect_timeout_s=TCP_CONNECT_TIMEOUT_S
        )

        if PLOT_REALTIME:
            fig, ax, raw_line, filtered_line, buttons = setup_plot()

        while running:
            infrared_values = read_wifi_infrared_values(wifi_client)

            if not infrared_values:
                if PLOT_REALTIME:
                    plt.pause(0.001)
                else:
                    time.sleep(0.001)
                continue

            for infrared_value in infrared_values:
                if PLOT_REALTIME and fig is not None:
                    if not plt.fignum_exists(fig.number):
                        running = False
                        break

                sample_count += 1

                raw_infrared_buffer.append(infrared_value)

                if signal_filter is None:
                    filtered_infrared_value = infrared_value
                else:
                    filtered_infrared_value = signal_filter.filter(infrared_value)

                filtered_infrared_buffer.append(filtered_infrared_value)

                print(
                    f"Infrared: {infrared_value:.2f} | "
                    f"Filtered Infrared: {filtered_infrared_value:.2f}"
                )

                if sample_count < initial_buffer_samples:
                    if PLOT_REALTIME:
                        plt.pause(0.001)
                    continue

                if PLOT_REALTIME and sample_count % PLOT_EVERY_N_SAMPLES == 0:
                    update_plot(
                        fig,
                        ax,
                        raw_line,
                        filtered_line,
                        raw_infrared_buffer,
                        filtered_infrared_buffer
                    )

    except KeyboardInterrupt:
        print("\nStopping from keyboard interrupt...")

    except (ConnectionError, OSError) as error:
        print(f"WiFi TCP error: {error}")

    finally:
        running = False

        if wifi_client is not None:
            wifi_client.close()
            print("WiFi TCP connection closed")

        if PLOT_REALTIME:
            plt.ioff()
            plt.show()


if __name__ == "__main__":
    main()