# 🥏 UDisc Stats Analyzer

UDisc Stats Analyzer is a Python-based application that imports and analyzes CSV
score data exported from UDisc — the popular disc golf score tracking app. It
processes player and course data to generate detailed statistics, helping disc
golf enthusiasts gain insights into their gameplay and performance trends. 📈

This repository contains a Python script to generate different types of stats
based on your UDisc golf games. Follow the [⚙️ Setup](#-setup) to install the
prerequisit Python packages and preparing your UDisc CSV files for analysis.

After completing the setup, continue to the [🔍 Analysis](#-analysis) section to
learn about the different analytics, and how to use them.

## ⚙️ Setup

### 🧩 Prerequisites

Set up your Python environment by installing the required Python packages. It is
recommended to do this in a virtual environment in order to not pollute your
default Python environment.

Create and enter a virtual environment:

```
python3 -m venv venv
source venv/bin/activate
```

Now, install the required Python packages:

```
pip install -r requirements.txt
```

✅ Your Python environment is now ready to use UDisc Stats Analyzer!

### 📂 Prepare UDisc CSV Files

Use the UDisc app to download the CSV files you want to analyze.

Move the CSV files into a separate directory named e.g., `score_cards`.

## 🔍 Analysis

The udisc_analysis.py script lets you generate different kinds of analytics from
your UDisc data. Use a subcommand to select the type of analysis you want to
run.

Use `python udisc_analysis.py -h` to get info about the subcommands, and
`python udisc_analysis.py <SUBCOMMMAND> -h` for more info about a specific
subcommand.

### ⛳ Hole Distribution

Plot the hole distribution with the `hole-distribution` subcommand:

```
python udisc_analysis.py hole-distribution --csv-dir score_cards --course Vipan --layout Main
```

Which generates a plot, such as:

![hole-distribution-demo](docs/hole-distribution-demo.png)

### 📉 Performance Curve

Plot performance curve with the `performance-curve` subcommand:

```
python udisc_analysis.py performance-curve --csv-dir score_cards --course Vipan --layout Main
```

Which generates a plot, such as:

![performance-curve-demo](docs/performance-curve-demo.png)

### 🎯 Score Distribution

Plot the score distribution with the `score-distribution` subcommand:

```
python udisc_analysis.py score-distribution --course Vipan --layout Main --csv-dir score_cards
```

Which generates a plot, such as:

![score-distribution-demo](docs/score-distribution-demo.png)

### 🧮 Basic Stats

Print basic stats with the `basic-stats` subcommand:

```
python udisc_analysis.py basic-stats --csv-dir score_cards --course Vipan --layout Main
```

See example output in [docs/basic-stats-demo.txt](./docs/basic-stats-demo.txt).
