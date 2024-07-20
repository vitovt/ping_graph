# Competitors

I tried to find ready tool but didn't fund something suitable. Here is short summary of what I've found:

## Comparing with Similar Programs

### [ping-graph-python](https://github.com/M1sterGlass/ping-graph-python)

Simple python app. Easy to run.

**Pros**:
- Allows adding IP or hostname via a TK GUI window for convenience.

**Cons**:
- The program encountered issues during testing. After installing dependencies and running the script, it only displayed a white window without rendering the graph. The CLI showed `| WARNING | Waiting for connection...` without further progress.

### [ping-plot](https://github.com/kartikmehta8/ping-plot)

Also simple python app.

**Pros**:
- The tool works and offers similar functionality for real-time ping monitoring and graphing.

**Cons**:
- Provides fewer statistics compared to Network Ping Monitor.
- Does not display timeouts or handle packet loss effectively; it simply connects the last successful ping with the next one on the graph.

### [ping-graph](https://github.com/adilurfaisal/ping-graph)
**Pros**:
- Capable of pinging multiple targets simultaneously.

**Cons**:
- Requires NodeJS installation and runs without a GUI, relying solely on the CLI.
- Does not account for lost packets, only shows the average ping.

### [lagraph](https://github.com/Calinou/lagraph)
**Pros**:
- Written in Rust and operates in the CLI, showing each ping as a separate line.

**Cons**:
- Lacks statistical analysis and does not handle lost packets or timeouts.

### [ping-graph](https://github.com/rstacruz/ping-graph)
**Pros**:
- A NodeJS CLI tool that visualizes pings and handles packet loss.

**Cons**:
- No numerical statistics provided.
- The project is outdated, with the last update over seven years ago, and it failed to run during testing.

### [gping](https://github.com/orf/gping)

A Rust-based application that is up-to-date and displays a graph using CLI graphics.
It lacks a GUI, relying entirely on the CLI.
The best of all previous, but also lack of functionality. But don't requre gui.

**Pros**:
- Shows some statistics and can ping multiple hosts concurrently.
- Robust handling of network interruptions.
- Docker ready
- had a lot of options, including ipv4 or ipv6
- Can ping multiple hosts together
- Don't crash or broke if network disappears for some time

**Cons**:
- Does not display detailed statistics for lost packets and timeouts.
- Although highly functional, 

