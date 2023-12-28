import subprocess
import re
import time
import matplotlib.pyplot as plt
import argparse
import threading

def ping(host):
    while True:
        # Run the ping command
        process = subprocess.Popen(["ping", host, "-c", "1"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, error = process.communicate()

        if process.returncode == 0:
            # Extract the time from the output
            match = re.search(r"time=(\d+.\d+) ms", out.decode('utf-8'))
            if match:
                delay = float(match.group(1))
                times.append(delay)
                timestamps.append(time.time() - start_time)
        else:
            print(f"Failed to ping {host}")

        time.sleep(1)

def plot():
    plt.ion()
    fig, ax = plt.subplots()
    while True:
        ax.clear()
        ax.plot(timestamps, times)
        ax.set_title(f"Ping response times to {host}")
        ax.set_xlabel('Time (seconds)')
        ax.set_ylabel('Response Time (ms)')
        ax.relim()
        ax.autoscale_view()
        plt.pause(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Ping a host and plot response time.')
    parser.add_argument('host', type=str, help='The host to ping')
    args = parser.parse_args()

    host = args.host
    times = []
    timestamps = []
    start_time = time.time()

    # Start the ping thread
    ping_thread = threading.Thread(target=ping, args=(host,))
    ping_thread.start()

    # Start the plotting thread
    plot_thread = threading.Thread(target=plot)
    plot_thread.start()

    ping_thread.join()
    plot_thread.join()

