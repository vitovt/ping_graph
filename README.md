# Network Ping Monitor

## Description

The Network Ping Monitor is a Python-based tool designed to continuously monitor network latency by pinging a specified host and visualizing the response times in real-time. This tool is particularly useful for network administrators, IT professionals, and anyone needing to monitor and analyze the stability and performance of their network connections. The script provides a live graph of ping response times and includes various statistics like average, minimum, maximum, and current response times, as well as standard deviation, to help identify and analyze network issues.

![Ping Monitor main window](screenshots/main_window.png?raw=true)

![Ping Monitor main window](screenshots/screenshot2.png?raw=true)

![Network Lost vizualization](screenshots/screenshot_with_losts.png?raw=true)

## Inspiration
The tool was inspired by [mtr tool](https://github.com/traviscross/mtr) but it lacks graph visualisation of pings.

I did some research, tried to find ready tool. Here is [short summary of what I've found](COMPETITORS.md).

But no one solution I've found satisfied my requirements. So I wrote my own solution.

The Network Ping Monitor stands out by providing comprehensive statistics, including **timeouts** and packet **loss**, along with a dynamic, real-time graphing capability within a GUI. This makes it particularly user-friendly and informative for monitoring and analyzing network performance.

## Features

- **Real-time Ping Monitoring**: Continuously pings a specified host and records response times.
- **Dynamic Graph Plotting**: Live updates of a plot graph displaying ping response times.
- **Auto-scaling Graph**: The graph auto-scales to accommodate varying response times.
- **Network Statistics Display**: Shows current, average, maximum, and minimum response times, along with the standard deviation, network losts and delays.
- **Vital parameters for VOIP applications**: Jitter and max number of sequental losts.
- **Command-line Interface**: Easy to use command-line interface for setting up the host to be pinged.
- **Multi-threaded Design**: Utilizes threading for simultaneous data collection and graph updating.
- **IPv6 support**: Supports IPv6 ip's and domains.

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

## Usage

Run the script from the command line, specifying the host to ping as an argument:

```sh
python network_ping_monitor.py [host]
```

Replace `[host]` with the hostname or IP address you want to monitor (e.g., `google.com`).

### Arguments

- `host`: The hostname or IP address to ping.

#### Optional Arguments

- `-W`, `--timeout`: Timeout in milliseconds for each ping request. Default is 150 milliseconds.
- `-i`, `--interval`: Interval between pings in seconds. Default is 0.1 second.
- `-D`, `--dead_timeout`: Execution timeout in milliseconds for each ping command. Default is 500 milliseconds. Maximum is 10,000 milliseconds. Must be greater than or equal to `timeout`.
- `-6`, `--ipv6`: Use IPv6 address for the ping.

### How Timeouts Work

- `-W`, `--timeout`: This is the timeout value for each individual ping request. If a ping response takes longer than this value, it is considered a timeout, and the response time is recorded as the timeout value.
- `-D`, `--dead_timeout`: This is the maximum time allowed for the `ping` command to execute. If the `ping` command takes longer than this value, it is forcibly terminated, and the response time is recorded as the `dead_timeout` value. This ensures that the script does not hang indefinitely if the network is down or the host is unreachable.

## Example

```sh
python network_ping_monitor.py google.com
```

This command will start pinging `google.com` and open a window displaying the live graph and statistics.

## License

[GPLv3]

## Contributing

Contributions to the Network Ping Monitor are welcome. Please read the contributing guidelines before submitting pull requests.

## Support and Contact

For support, feature requests, or any queries, please open an issue in the GitHub repository.
