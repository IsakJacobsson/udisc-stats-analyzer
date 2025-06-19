# UDisc Stats Analyzer

UDisc Stats Analyzer is a Python-based application that imports and analyzes CSV
score data exported from UDisc — the popular disc golf score tracking app. It
processes player and course data to generate detailed statistics, helping disc
golf enthusiasts gain insights into their gameplay and performance trends.

This repository contains Python scripts to plot different types of stats based
on your UDisc golf games. Follow the [Setup](#setup) to instal the prerequisit
Python packages and preparing your UDisc CSV files for analysis.

After completing the setup, continue to the [Scripts](#scripts) section to learn
about which scripts are available, and how to use them.

## Setup

### Prerequisites

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

Your Python environment is now ready to use UDisc Stats Analyzer!

### Prepare UDisc CSV Files

Use the UDisc app to download the CSV files you want to analyze.

Move the CSV files into a separate directory named e.g., `score_cards`.

## Scripts

In the following section, all available scripts will be introduced and a breif
instruction of how to use the script will be provided.

### Course Analysis

Plot the course analysis for a specific course by running the
`course_analysis.py` script.

This script will generate a boxplot with the distribution per hole for a
specific course and layour. It is possible to choose what player(s) to include
in the plot.

Here is an example use for course "Vipan" and layout "Main" for all players.
Remember to always specify the directory containing your UDisc CSV files:

```
python course_analysis.py --csv-dir score_cards --course Vipan --layout Main
```

Which generates a plot, such as:

![course-analysis-demo](docs/course-analysis-demo.png)

To specify for what player(s) to include in the plot, add one or more players by
using the `-p` or `--player` option:

```
python course_analysis.py -d score_cards -c Vipan --layout Main -p 'Isak ”Bush Walker” Jacobsson' -p Johanna
```

For more options and help for how to use the `course_analysis.py` script
run the help command:

```
python course_analysis.py -h
```

### Performance Over Time

Plot performace over time with the `performance_over_time.py` script.

This script will generate a lineplot with the score over time for a specific
stat, such as total round score or a specific hole. It is possible to choose
what player(s) to draw lines for.

Provide the directory containing the UDisc CSV files, course, layout, and
optionally the player(s) to plot for. By default all players with at least one
record of the selecet stat will be plotted. When not specifiying a stat, the
script will generate a plot for total round score. Here is an example:

```
python performance_over_time.py --csv-dir score_cards --course Vipan --layout Main
```

Which generates a plot, such as:

![performance-over-time-demo](docs/performance_over_time.png)

To specify a specific stat, use the `-s` or `--stat` option followed by e.g.
`Hole1`.

```
python performance_over_time.py -d score_cards -c Vipan --layout Main -s Hole1
```

For more options and help for how to use the `performance_over_time.py` script
run the help command:

```
python performance_over_time.py -h
```
