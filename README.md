# UDisc Stats Analyzer

UDisc Stats Analyzer is a small Python tool for digging into your disc golf
rounds exported from UDisc. It reads the CSV scorecards you download from the
app and turns them into useful stats and plots, so you can get a better feel for
how you’re actually playing over time.

The goal of this project is pretty simple: make it easy to explore your own
UDisc data without a lot of manual work. If you’re curious about score
distributions, consistency, or how your performance changes round to round, this
script can help.

This repository contains a single Python script that can generate several
different kinds of statistics from your UDisc games. Start with the setup
instructions below to install the required Python packages and prepare your CSV
files. After that, head to the analysis section to see what kinds of stats you
can generate and how to run them.

## Setup

### Prerequisites
You’ll need Python 3 installed. The required Python packages are listed in
`requirements.txt`. It’s recommended to install them in a virtual environment so
you don’t affect your system-wide Python setup.

Create and activate a virtual environment:

```
python3 -m venv venv
source venv/bin/activate
```

Then install the dependencies:

```
pip install -r requirements.txt
```

### Prepare UDisc CSV Files

Use the UDisc app to export the CSV files you want to analyze as CSV files.

Create a directory for them (for example, `score_cards`) and move all exported
CSV files into that directory. The script will read all CSV files found there.

## Analysis

The `udisc_analysis.py` script supports several different types of analysis.
Each type is selected using a subcommand.

To see an overview of all available subcommands:

```
python udisc_analysis.py -h
```

To get detailed help for a specific subcommand:

```
python udisc_analysis.py <SUBCOMMAND> -h
```

Below are the supported analyses.

### Hole Distribution

Shows how your scores are distributed per hole for a given course and layout.

Example:

```
python udisc_analysis.py hole-distribution --csv-dir score_cards --course Vipan --layout Main
```

This generates a plot like the one below:

![hole-distribution-demo](docs/hole-distribution-demo.png)

### Performance Curve

Plots a performance curve to visualize how your scoring develops over time.

Example:

```
python udisc_analysis.py performance-curve --csv-dir score_cards --course Vipan --layout Main
```

Example output:

![performance-curve-demo](docs/performance-curve-demo.png)

### Score Distribution

Shows how often different total scores occur for a given course and layout.

Example:

```
python udisc_analysis.py score-distribution --course Vipan --layout Main --csv-dir score_cards
```

Example output:

![score-distribution-demo](docs/score-distribution-demo.png)

### Basic Stats

Prints a set of basic statistics, such as averages and simple aggregates,
directly to the terminal.

Example:

```
python udisc_analysis.py basic-stats --csv-dir score_cards --course Vipan --layout Main
```

An example of the output can be found in [docs/basic-stats-demo.txt](./docs/basic-stats-demo.txt).
