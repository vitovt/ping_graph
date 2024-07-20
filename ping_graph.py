#!/usr/bin/env python3

import subprocess
import re
import time as tme
import matplotlib.pyplot as plt
import argparse
import threading
import numpy as np
import socket
import sys

def ping(host, times, pings, timeout, dead_timeout, interval):
    ping_count = 0
    global running
    while running:
        # Run the ping command with a timeout
        command = ["timeout", str(dead_timeout / 1000), "ping", host, "-c", "1", "-W", str(timeout)]
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
                    times.append(delay)
                    pings.append(ping_count)
                else:
                    times.append(delay)
                    pings.append(ping_count)
        elif process.returncode == 124:
            # Ping didn't return in reasonable time
            # 124 is the exit code for timeout command if it reaches the timeout
            print(f"Ping to {host} execution timed out after {dead_timeout} milliseconds")
            times.append(dead_timeout)
            pings.append(ping_count)
        else:
            # Ping didn't return in reasonable time
            # Other reason, like Network Unreachable, etc ...
            print(f"Failed to ping {host} or request timed out with error: {error.decode('utf-8')}")
            # Mark lost ping as timeout value
            times.append(dead_timeout)
            pings.append(ping_count)

        tme.sleep(interval)

def update_stats(ax, times, timeout, dead_timeout, start_time):
    if times:
        total_running_time = tme.time() - start_time
        valid_times = [time for time in times if time != timeout and time != dead_timeout]
        avg_time = np.mean(valid_times)
        max_time = np.max([time for time in times if time != dead_timeout])
        min_time = np.min(valid_times)
        std_dev = np.std(valid_times)

        # Calculate jitter as the average of the absolute differences between consecutive ping times
        jitter = np.mean([abs(valid_times[i] - valid_times[i - 1]) for i in range(1, len(valid_times))])

        # Calculate the percentage of times greater than timeout
        times_greater_than_timeout = len([time for time in times if time > timeout])
        percentage_greater_than_timeout = (times_greater_than_timeout / len(times)) * 100

        # Calculate the percentage of lost packets (where time == dead_timeout)
        times_lost = len([time for time in times if time == dead_timeout])
        percentage_lost = (times_lost / len(times)) * 100

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
    global running
    running = False
    print('Close event')

def resolve_hostname(host):
    try:
        ip = socket.gethostbyname(host)
        return ip
    except socket.gaierror as e:
        print(f"Failed to resolve hostname {host} with error: {e}")
        return None

if __name__ == "__main__":
    running = True
    parser = argparse.ArgumentParser(description='Ping a host and plot response time.', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('host', type=str, help='The host to ping')
    parser.add_argument('-W', '--timeout', type=int, default=150, help='Timeout in milliseconds for each ping request')
    parser.add_argument('-i', '--interval', type=float, default=0.1, help='Interval between pings in seconds. Default is 0.1 second.')
    parser.add_argument('-D', '--dead_timeout', type=float, default=500, help='Execution timeout in milliseconds for each ping command.\nDefault is 500 milliseconds.\nMaximum is 10,000 milliseconds.\nMust be more or equal to timeout')

    args = parser.parse_args()

    host = args.host
    timeout = args.timeout
    interval = args.interval
    dead_timeout = args.dead_timeout
    if dead_timeout > 10000 or dead_timeout < timeout:
        sys.exit(f"Dead timeout (-D) value {dead_timeout} out of range. Exiting.")

    resolved_host = resolve_hostname(host)
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
    while running:
        if pings:
            ax.clear()
            ax.plot(pings, times, color='green')
            # Highlight timeouts in red
            ax.scatter(
                [p for p, t in zip(pings, times) if t >= timeout and t != dead_timeout],
                [timeout] * len([t for t in times if t >= timeout and t != dead_timeout]),
                color='red'
            )

            # Highlight dead timeouts in another color
            ax.scatter(
                [p for p, t in zip(pings, times) if t == dead_timeout],
                [dead_timeout] * len([t for t in times if t == dead_timeout]),
                color='magenta'
            )
            ax.set_title(f"Ping response times to {host}")
            ax.set_xlabel('Number of Pings')
            ax.set_ylabel('Response Time (ms)')
            ax.relim()
            ax.autoscale_view()

            update_stats(ax, times, timeout, dead_timeout, start_time)

        plt.pause(1)
    print('Exiting ...')
    ping_thread.join(2)
    print('Waiting last ping finishes ...')

