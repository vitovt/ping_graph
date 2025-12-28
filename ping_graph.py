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
import platform

# Synchronization primitives for thread-safe data access and clean shutdown
data_lock = threading.Lock()
stop_event = threading.Event()

# Completed results: probe_id -> rtt_ms (uses dead_timeout for timeouts/loss)
results: dict[int, float] = {}
inflight: set[int] = set()

TIME_RE = re.compile(r"time(?P<cmp>[=<])\s*(?P<val>\d+(?:\.\d+)?)\s*ms", re.IGNORECASE)

def build_ping_cmd(host: str, per_packet_timeout_ms: int, use_ipv6: bool) -> list[str]:
    """
    Return a platform-appropriate ping command that sends exactly 1 probe and
    uses per-packet timeout close to `per_packet_timeout_ms` when supported.
    """
    os_name = platform.system()
    ip_flag = "-6" if use_ipv6 else "-4"

    if os_name == "Windows":
        # Windows ping:
        #   -n 1  : one echo
        #   -w ms : per-reply timeout in milliseconds
        #   -6/-4 : force IP family
        return ["ping", ip_flag, "-n", "1", "-w", str(int(per_packet_timeout_ms)), host]

    elif os_name == "Darwin":
        # macOS/BSD ping:
        #   -c 1  : one echo
        #   -W ms : per-reply timeout in *milliseconds* (BSD)
        #   -6/-4 : force IP family
        return ["ping", ip_flag, "-c", "1", "-W", str(int(per_packet_timeout_ms)), host]

    else:
        # Linux (iputils ping):
        #   -c 1     : one echo
        #   -W secs  : per-reply timeout in *seconds* (float allowed)
        #   -6/-4    : force IP family
        secs = max(0.001, per_packet_timeout_ms / 1000.0)
        return ["ping", ip_flag, "-c", "1", "-W", f"{secs:.3f}", host]

def parse_ping_time(output_text: str) -> float | None:
    """
    Parse RTT from ping output in milliseconds.
    Handles 'time=12.3 ms', 'time=12ms', and 'time<1ms'.
    Returns None if it cannot parse.
    """
    m = TIME_RE.search(output_text)
    if not m:
        return None
    val = float(m.group("val"))
    # If comparator was '<', we conservatively use the reported bound (e.g., 1ms).
    # You could choose val/2.0 if you'd rather approximate.
    return val

def run_single_probe(probe_id: int, host: str, timeout_ms: int, dead_timeout: int, use_ipv6: bool):
    """Run one ping in the background, record its outcome, never block the scheduler."""
    cmd = build_ping_cmd(host, per_packet_timeout_ms=int(dead_timeout), use_ipv6=use_ipv6)

    with data_lock:
        inflight.add(probe_id)

    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            # Enforce a hard deadline for the whole ping invocation (cross-platform)
            out, error = process.communicate(timeout=max(0.001, dead_timeout / 1000.0))
            rc = process.returncode
        except subprocess.TimeoutExpired:
            # If the process exceeded dead_timeout, kill it and mark as lost
            try:
                process.kill()
            except Exception:
                pass
            out, error = process.communicate()
            rc = 124  # synthetic 'timeout' code to mirror prior logic

        out_text = (out or b"").decode("utf-8", errors="ignore")
        err_text = (error or b"").decode("utf-8", errors="ignore")

        if rc == 0:
            delay = parse_ping_time(out_text)
            if delay is None:
                # Could not parse RTT from a "successful" ping → treat as timeout ceiling
                print(f"No [{probe_id}] RTT parse failed, recording as {dead_timeout} ms")
                measured = float(dead_timeout)
            else:
                if delay > timeout_ms:
                    print(f"No [{probe_id}] Slow reply: {delay:.2f} ms (> {timeout_ms} ms)")
                measured = float(delay)
        elif rc == 124:
            # Our hard deadline expired
            print(f"No [{probe_id}] Ping execution timed out after {dead_timeout} ms")
            measured = float(dead_timeout)
        else:
            # Non-zero exit (host unreachable, no route, etc.)
            # Record as lost with dead_timeout marker
            msg = err_text.strip() or out_text.strip() or f"exit code {rc}"
            print(f"No [{probe_id}] Ping failed: {msg}")
            measured = float(dead_timeout)

    except Exception as e:
        print(f"No [{probe_id}] Probe crashed: {e}")
        measured = float(dead_timeout)

    # Commit the result
    with data_lock:
        results[probe_id] = measured
        inflight.discard(probe_id)

def update_stats(ax, completed_times, timeout, dead_timeout, start_time, n_scheduled, n_inflight):
    total_running_time = tme.time() - start_time

    # Ensure variables exist even when there are no samples yet
    gt_timeout = 0
    lost = 0
    max_seq = 0

    if completed_times:
        valid_times = [t for t in completed_times if t != dead_timeout]
        avg_time = np.mean(valid_times) if valid_times else 0.0
        min_time = np.min(valid_times) if valid_times else 0.0
        std_dev  = np.std(valid_times) if valid_times else 0.0
        if len(valid_times) > 1:
            jitter = np.mean([abs(valid_times[i] - valid_times[i-1]) for i in range(1, len(valid_times))])
        else:
            jitter = 0.0
        max_time = np.max(valid_times) if valid_times else 0.0

        gt_timeout = sum(1 for t in completed_times if (t >= timeout and t != dead_timeout))
        pct_gt_timeout = (gt_timeout / len(completed_times)) * 100.0

        lost = sum(1 for t in completed_times if t == dead_timeout)
        pct_lost = (lost / len(completed_times)) * 100.0

        # longest consecutive ≥ timeout (including "lost")
        cur_seq = 0
        for t in completed_times:
            if (t >= timeout and t != dead_timeout) or (t == dead_timeout):
                cur_seq += 1
                if cur_seq > max_seq:
                    max_seq = cur_seq
            else:
                cur_seq = 0
    else:
        avg_time = min_time = max_time = std_dev = jitter = 0.0
        pct_gt_timeout = pct_lost = 0.0

    stats_text = (
        f'Average: {avg_time:.2f} ms\n'
        f'Max: {max_time:.2f} ms\n'
        f'Min: {min_time:.2f} ms\n'
        f'Std Dev: {std_dev:.2f} ms\n'
        f'Jitter: {jitter:.2f} ms\n'
        f'% Timeout(>): {pct_gt_timeout:.2f}%\n'
        f'% Lost(=): {pct_lost:.2f}%\n'
        f'N scheduled: {n_scheduled}\n'
        f'N done: {len(completed_times)}\n'
        f'N inflight: {n_inflight}\n'
        f'N timeout: {gt_timeout}\n'
        f'Max N SEQ tim.: {max_seq}\n'
        f'N lost: {lost}\n'
        f'---settings---\n'
        f'-W timeout: {timeout} ms\n'
        f'-D: {dead_timeout} ms\n'
        f'-i interval: {args.interval} s\n\n'
        f'RunTime: {total_running_time:.2f} s\n\n'
        f'Press "q" to quit'
    )
    ax.text(0.30, 0.95, stats_text, transform=ax.transAxes,
            fontsize=10, va='top', ha='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

def on_close(event):
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
    parser.add_argument('-W', '--timeout', type=int, default=150, help='Classification threshold in milliseconds for marking a reply as slow')
    parser.add_argument('-i', '--interval', type=float, default=0.1, help='Interval between pings in seconds. Default is 0.1 second.')
    parser.add_argument('-D', '--dead_timeout', type=float, default=500, help=('Hard deadline in milliseconds per ping invocation. '
                              'Used to kill the ping process if it hangs. '
                              'Default is 500 ms; max is 10,000 ms; must be >= --timeout'))
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

    start_time = tme.time()

    # Matplotlib setup
    plt.ion()
    fig, ax = plt.subplots()

    fig.canvas.mpl_connect('close_event', on_close)

    # Create a button to toggle the Y scale
    ax_button = plt.axes([0.05, 0.01, 0.07, 0.075])
    btn = Button(ax_button, 'Log. Y')
    btn.on_clicked(toggle_scale)

    # Probe scheduling (non-blocking) -----------------------------------------
    probe_id = 0
    next_send = tme.monotonic()  # precise scheduler

    try:
        while not stop_event.is_set():
            now = tme.monotonic()

            # Fire as many probes as needed to "catch up" if UI loop lags
            while now >= next_send and not stop_event.is_set():
                probe_id += 1
                threading.Thread(
                    target=run_single_probe,
                    args=(probe_id, resolved_host, timeout, int(dead_timeout), args.ipv6),
                    daemon=True
                ).start()
                next_send += interval

            # Snapshot results for plotting
            with data_lock:
                done_ids = sorted(results.keys())
                times_snapshot = [results[i] for i in done_ids]
                pings_snapshot = done_ids[:]  # x-axis by probe id
                inflight_count = len(inflight)
                n_scheduled = probe_id

            ax.clear()

            if pings_snapshot:
                ax.plot(pings_snapshot, times_snapshot, color='green')

                # Highlight timeouts in red
                # Highlight slow (> timeout, but not killed)
                xs = [p for p, t in zip(pings_snapshot, times_snapshot) if t >= timeout and t != dead_timeout]
                ys = [timeout] * len(xs)
                ax.scatter(xs, ys, color='red')
                # Highlight dead timeouts in magenta
                # Highlight hard timeouts (killed at dead_timeout)
                xs_dead = [p for p, t in zip(pings_snapshot, times_snapshot) if t == dead_timeout]
                ys_dead = [dead_timeout] * len(xs_dead)
                ax.scatter(xs_dead, ys_dead, color='magenta')

            ax.set_yscale(current_scale)
            ax.set_title(f"Ping response times to {'IPv6 ' if args.ipv6 else 'IPv4 '}{host}")
            ax.set_xlabel('Number of Pings')
            ax.set_ylabel('Response Time (ms)')
            ax.relim()
            ax.autoscale_view()

            update_stats(ax, times_snapshot, timeout, dead_timeout, start_time,
                         n_scheduled=n_scheduled, n_inflight=inflight_count)


            fig.canvas.start_event_loop(0.2)
    except KeyboardInterrupt:
        stop_event.set()
        plt.close(fig)
        print('Interrupted, shutting down...')
    print('Exiting ...')
    print('Waiting last ping finishes ...')
    # We don’t forcibly join probe threads here; they exit after their own deadlines.

