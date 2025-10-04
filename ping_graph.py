#!/usr/bin/env python3

import subprocess
import re
import time as tme
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import argparse
import threading
import numpy as np
import socket
import sys
 
# Synchronization primitives for thread-safe data access and clean shutdown
data_lock = threading.Lock()
stop_event = threading.Event()

def ping(host, times, pings, timeout, dead_timeout, interval):
    ping_count = 0
    global stop_event, data_lock
    while not stop_event.is_set():
        # Run the ping command with a timeout
        command = ["timeout", str(dead_timeout / 1000), "ping6" if args.ipv6 else "ping", host, "-c", "1", "-W", str(timeout)]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, error = process.communicate()

        ping_count += 1
        # Ping returns successfully
        if process.returncode == 0:
            # Extract the time from the output
            match = re.search(r"time=(\d+.\d+) ms", out.decode('utf-8'))
            if match:
                delay = float(match.group(1))
                # Check if the delay exceeds the timeout
                if delay > timeout:
                    print(f"Ping response time {delay} ms exceeded timeout of {timeout} ms")
                    # don't Treat LONG delay as timeout
                    with data_lock:
                        times.append(delay)
                        pings.append(ping_count)
                else:
                    with data_lock:
                        times.append(delay)
                        pings.append(ping_count)
        elif process.returncode == 124:
            # Ping didn't return in reasonable time
            # 124 is the exit code for timeout command if it reaches the timeout
            print(f"Ping to {host} execution timed out after {dead_timeout} milliseconds")
            with data_lock:
                times.append(dead_timeout)
                pings.append(ping_count)
        else:
            # Ping didn't return in reasonable time
            # Other reason, like Network Unreachable, etc ...
            print(f"Failed to ping {host} or request timed out with error: {error.decode('utf-8')}")
            # Mark lost ping as timeout value
            with data_lock:
                times.append(dead_timeout)
                pings.append(ping_count)

        tme.sleep(interval)

def update_stats(ax, times, timeout, dead_timeout, start_time):
    if times:
        total_running_time = tme.time() - start_time
        valid_times = [time for time in times if time != dead_timeout]

        if valid_times:
            avg_time = np.mean(valid_times)
            min_time = np.min(valid_times)
            std_dev = np.std(valid_times)
            # Calculate jitter as the average of the absolute differences between consecutive ping times
            if len(valid_times) > 1:
                jitter = np.mean([abs(valid_times[i] - valid_times[i - 1]) for i in range(1, len(valid_times))])
            else:
                jitter = 0
        else:
            avg_time = min_time = std_dev = jitter = 0

        max_time = np.max(valid_times) if valid_times else 0

        # Calculate the percentage of times greater than timeout
        times_greater_than_timeout = len([time for time in times if time > timeout])
        percentage_greater_than_timeout = (times_greater_than_timeout / len(times)) * 100 if times else 0

        # Calculate the percentage of lost packets (where time == dead_timeout)
        times_lost = len([time for time in times if time == dead_timeout])
        percentage_lost = (times_lost / len(times)) * 100 if times else 0

        # Calculate the maximum sequential number of times >= timeout
        total = 0
        total_timeout = 0
        total_lost = 0
        max_sequential_timeout = 0
        current_sequence_timeout = 0
        for time in times:
            if time >= timeout and time != dead_timeout:
                total_timeout += 1
                current_sequence_timeout += 1
            elif time == dead_timeout:
                total_lost += 1
                current_sequence_timeout += 1
            else:
                total += 1
                current_sequence_timeout = 0

            # Calculate the maximum sequential number of times >= timeout
            if current_sequence_timeout > max_sequential_timeout:
                max_sequential_timeout = current_sequence_timeout

        stats_text = (
            f'Average: {avg_time:.2f} ms\n'
            f'Max: {max_time:.2f} ms\n'
            f'Min: {min_time:.2f} ms\n'
            f'Std Dev: {std_dev:.2f} ms\n'
            f'Jitter: {jitter:.2f} ms\n'
            f'% Timeout(>): {percentage_greater_than_timeout:.2f}%\n'
            f'% Lost(=): {percentage_lost:.2f}%\n'
            f'total N:{len(times)}\n'
            f'N timeout: {total_timeout}\n'
            f'Max N SEQ tim.: {max_sequential_timeout}\n'
            f'N lost: {total_lost}\n'
            f'---settings---\n'
            f'-W timeout: {timeout} ms\n'
            f'-D: {dead_timeout}ms\n'
            f'-i interval: {interval} s\n\n'
            f'RunTime: {total_running_time:.2f} s\n\n'
            f'Press "q" to quit'
        )
        ax.text(0.3, 0.95, stats_text, transform=ax.transAxes, fontsize=10, verticalalignment='top', horizontalalignment='right', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

def on_close(event):
    global stop_event
    stop_event.set()
    print('Close event')

def resolve_hostname(host, use_ipv6):
    try:
        addrinfo = socket.getaddrinfo(host, None, socket.AF_INET6 if use_ipv6 else socket.AF_INET)
        return addrinfo[0][4][0]
    except socket.gaierror as e:
        print(f"Failed to resolve hostname {host} with error: {e}")
        return None

def toggle_scale(event):
    global current_scale
    current_scale = 'log' if current_scale == 'linear' else 'linear'
    ax.set_yscale(current_scale)
    plt.draw()

if __name__ == "__main__":
    current_scale = 'linear'
    parser = argparse.ArgumentParser(description='Ping a host and plot response time.', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('host', type=str, help='The host to ping')
    parser.add_argument('-W', '--timeout', type=int, default=150, help='Timeout in milliseconds for each ping request')
    parser.add_argument('-i', '--interval', type=float, default=0.1, help='Interval between pings in seconds. Default is 0.1 second.')
    parser.add_argument('-D', '--dead_timeout', type=float, default=500, help='Execution timeout in milliseconds for each ping command.\nDefault is 500 milliseconds.\nMaximum is 10,000 milliseconds.\nMust be more or equal to timeout')
    parser.add_argument('-6', '--ipv6', action='store_true', help='Use IPv6 for the ping')

    args = parser.parse_args()

    host = args.host
    timeout = args.timeout
    interval = args.interval
    dead_timeout = args.dead_timeout
    if dead_timeout > 10000 or dead_timeout < timeout:
        sys.exit(f"Dead timeout (-D) value {dead_timeout} out of range. Exiting.")

    resolved_host = resolve_hostname(host, args.ipv6)
    if not resolved_host:
        sys.exit(f"Could not resolve host {host}. Exiting.")

    times = []
    pings = []
    start_time = tme.time()

    # Start the ping thread
    ping_thread = threading.Thread(target=ping, args=(resolved_host, times, pings, timeout, dead_timeout, interval))
    ping_thread.start()

    plt.ion()
    fig, ax = plt.subplots()

    fig.canvas.mpl_connect('close_event', on_close)

    # Create a button to toggle the Y scale
    ax_button = plt.axes([0.05, 0.01, 0.07, 0.075])
    btn = Button(ax_button, 'Log. Y')
    btn.on_clicked(toggle_scale)

    try:
        while not stop_event.is_set():
            if pings:
                # Take thread-safe snapshots for plotting and stats
                with data_lock:
                    pings_snapshot = list(pings)
                    times_snapshot = list(times)

                ax.clear()
                ax.plot(pings_snapshot, times_snapshot, color='green')
            # Highlight timeouts in red
                ax.scatter(
                    [p for p, t in zip(pings_snapshot, times_snapshot) if t >= timeout and t != dead_timeout],
                    [timeout] * len([t for t in times_snapshot if t >= timeout and t != dead_timeout]),
                    color='red'
                )

            # Highlight dead timeouts in another color
                ax.scatter(
                    [p for p, t in zip(pings_snapshot, times_snapshot) if t == dead_timeout],
                    [dead_timeout] * len([t for t in times_snapshot if t == dead_timeout]),
                    color='magenta'
                )
            ax.set_yscale(current_scale)
            ax.set_title(f"Ping response times to {'IPv6 ' if args.ipv6 else 'IPv4 '}{host}")
            ax.set_xlabel('Number of Pings')
            ax.set_ylabel('Response Time (ms)')
            ax.relim()
            ax.autoscale_view()
            update_stats(ax, times_snapshot, timeout, dead_timeout, start_time)

            plt.pause(0.2)
    except KeyboardInterrupt:
        stop_event.set()
        plt.close(fig)
        print('Interrupted, shutting down...')
    print('Exiting ...')
    ping_thread.join(2)
    print('Waiting last ping finishes ...')

