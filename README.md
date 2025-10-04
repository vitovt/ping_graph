# Network Ping Monitor

## Description

**Network Ping Monitor** is a Python-based tool designed to continuously monitor network latency by pinging a specified host and visualizing the response times in real-time. This tool is particularly useful for network administrators, IT professionals, and anyone needing to monitor and analyze the stability and performance of their network connections. The script provides a live graph of ping response times and includes various statistics like average, minimum, maximum, and current response times, as well as standard deviation, to help identify and analyze network issues.
Now supports **Linux, macOS (**testers needed!**), and Windows** without requiring external wrappers like `timeout`.

![Ping Monitor main window](screenshots/main_window.png?raw=true)

![Ping Monitor main window](screenshots/screenshot2.png?raw=true)

![Network Lost vizualization](screenshots/screenshot_with_losts.png?raw=true)

## Inspiration
The tool was inspired by [mtr tool](https://github.com/traviscross/mtr) but it lacks graph visualisation of pings.

I did some research, tried to find ready tool. Here is [short summary of what I've found](COMPETITORS.md).

But no one solution I've found satisfied my requirements. So I wrote my own solution.

The Network Ping Monitor stands out by providing comprehensive statistics, including **timeouts** and packet **loss**, along with a dynamic, real-time graphing capability within a GUI. This makes it particularly user-friendly and informative for monitoring and analyzing network performance.

## Features

- **Cross-platform:** Works on **Linux**, **macOS**, and **Windows**. No GNU `timeout` required.
- **Real-time Ping Monitoring**: Continuously pings a specified host and records response times.
- **Dynamic Graph Plotting**: Live updates of a plot graph displaying ping response times.
- **Auto-scaling Graph**: The graph auto-scales to accommodate varying response times.
- **Network Statistics Display**: Shows current, average, maximum, and minimum response times, along with the standard deviation, network losts and delays.
- **Vital parameters for VOIP applications**: Jitter and max number of sequental losts.
- **Command-line Interface**: Easy to use command-line interface for setting up the host to be pinged.
- **Multi-threaded Design**: Utilizes threading for simultaneous data collection and graph updating.
- **IPv4/IPv6:** Force IP family with a flag.
- **Thread-safe design & graceful shutdown.**

## Requirements

- Python 3.x
- Matplotlib (`pip install matplotlib`)
- NumPy (`pip install numpy`)

## Installation

1. Clone the repository or download the script.
```sh
git clone git@github.com:vitovt/ping_graph.git
cd ping_graph
```
2. Ensure Python 3.x is installed on your system.
3. Install required Python packages: `matplotlib` and `numpy`.

OR

3. Install dependencies from `requirements.txt`:
```sh
pip install -r requirements.txt
```
*Warning!* New versions of Ubuntu doesn't support system-wide pip packages installations!
Use *venv*, it's mandatory!


## Usage

Run the script from the command line, specifying the host to ping as an argument:

```sh
python ping_graph.py [host]
# macOS/Linux may use:  python3 ping_graph.py [host]
# Windows (PowerShell): py -3 ping_graph.py [host]
```

Replace `[host]` with the hostname or IP address you want to monitor (e.g., `google.com`).

### Arguments

- `host`: The hostname or IP address to ping.

#### Optional arguments

* `-W`, `--timeout` (ms): **Threshold** for classifying a reply as “slow”.
  Used for **coloring** points on the graph and related stats.
  *Note: this does **not** change the OS ping timeout.*
- `-i`, `--interval`: Interval between pings in seconds. Default is 0.1 second.
* `-D`, `--dead_timeout` (ms): **Hard per-probe deadline.**
  The program enforces this both by passing an OS-specific per-reply timeout to `ping` **and** by killing the subprocess if it exceeds this deadline.
  Default: `500`. Range: `timeout` … `10000`.
* `-6`, `--ipv6`: Use IPv6 (default is IPv4).

### How Timeouts Work

- `-W`, `--timeout`: This is the timeout value for each individual ping request. If a ping response takes longer than this value, it is considered a timeout, and the response time is recorded as the timeout value.
- `-D`, `--dead_timeout`: This is the maximum time allowed for the `ping` command to execute. If the `ping` command takes longer than this value, it is forcibly terminated, and the response time is recorded as the `dead_timeout` value. This ensures that the script does not hang indefinitely if the network is down or the host is unreachable.

### Platform notes

The tool chooses appropriate flags for your OS automatically:

* **Windows:** `ping -n 1 -w <ms> -4/-6`
* **macOS (Darwin/BSD):** `ping -c 1 -W <ms> -4/-6`
* **Linux (iputils):** `ping -c 1 -W <seconds> -4/-6` (fractional seconds supported)

> Ensure `ping` is available in your `PATH`. On most systems it is installed by default.

### UI controls & exit

* **Log. Y** button toggles linear/logarithmic Y-axis.
* Exit by **closing the window** or pressing **Ctrl+C** in the terminal.

## Examples

```sh
# Basic
python ping_graph.py google.com

# IPv6 with a tighter hard deadline and slower probe rate
python ping_graph.py -6 -D 300 -i 0.5 ipv6.google.com

# Mark anything above 120 ms as “slow”
python ping_graph.py -W 120 1.1.1.1
```

## License

[GPLv3]

## Contributing

Contributions are welcome! Please open an issue or PR with a clear description and rationale.

## Support and Contact

For support or feature requests, open an issue in this repository.
