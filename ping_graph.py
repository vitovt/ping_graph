#!/usr/bin/env python3

import subprocess
import re
import time
import matplotlib.pyplot as plt
import argparse
import threading
import numpy as np

def ping(host, times, pings, timeout, interval):
    ping_count = 0
    while True:
        # Run the ping command with a timeout
        process = subprocess.Popen(["ping", host, "-c", "1", "-W", str(timeout)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, error = process.communicate()

        ping_count += 1
        if process.returncode == 0:
            # Extract the time from the output
            match = re.search(r"time=(\d+.\d+) ms", out.decode('utf-8'))
            if match:
                delay = float(match.group(1))
                # Check if the delay exceeds the timeout
                if delay > timeout:
                    print(f"Response time {delay} ms exceeded timeout of {timeout} ms")
                    # don't Treat LONG delay as timeout
                    times.append(delay)
                    pings.append(ping_count)
                else:
                    times.append(delay)
                    pings.append(ping_count)
        else:
            print(f"Failed to ping {host} or request timed out")
            # Mark lost ping as timeout value
            times.append(timeout)
            pings.append(ping_count)

        time.sleep(interval)

def update_stats(ax, times, timeout):
    if times:
        avg_time = np.mean([time for time in times if time != timeout])
        max_time = np.max(times)
        min_time = np.min([time for time in times if time != timeout])
        std_dev = np.std([time for time in times if time != timeout])

        # Calculate the percentage of times greater than timeout
        times_greater_than_timeout = len([time for time in times if time > timeout])
        percentage_greater_than_timeout = (times_greater_than_timeout / len(times)) * 100

        stats_text = f'Average: {avg_time:.2f} ms\nMax: {max_time:.2f} ms\nMin: {min_time:.2f} ms\nStd Dev: {std_dev:.2f} ms\n% Timeout(>=): {percentage_greater_than_timeout:.2f}%\n---settings---\n-W timeout: {timeout} ms\n-i interval: {interval} s'
        ax.text(0.3, 0.95, stats_text, transform=ax.transAxes, fontsize=10, verticalalignment='top', horizontalalignment='right', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Ping a host and plot response time.')
    parser.add_argument('host', type=str, help='The host to ping')
    parser.add_argument('-W', '--timeout', type=int, default=150, help='Timeout in milliseconds for each ping request')
    parser.add_argument('-i', '--interval', type=float, default=0.1, help='Interval between pings in seconds. Default is 0.1 second.')
    args = parser.parse_args()

    host = args.host
    timeout = args.timeout
    interval = args.interval
    times = []
    pings = []
    start_time = time.time()

    # Start the ping thread
    ping_thread = threading.Thread(target=ping, args=(host, times, pings, timeout, interval))
    ping_thread.start()

    plt.ion()
    fig, ax = plt.subplots()
    while True:
        if pings:
            ax.clear()
            ax.plot(pings, times, color='green')
            # Highlight timeouts in red
            ax.scatter([p for p, t in zip(pings, times) if t >= timeout], [timeout] * len([t for t in times if t >= timeout]), color='red')
            ax.set_title(f"Ping response times to {host}")
            ax.set_xlabel('Number of Pings')
            ax.set_ylabel('Response Time (ms)')
            ax.relim()
            ax.autoscale_view()

            update_stats(ax, times, timeout)

        plt.pause(1)

