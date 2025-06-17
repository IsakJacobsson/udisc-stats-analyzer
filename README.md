# UDisc Stats Analyzer

UDisc Stats Analyzer is a Python-based application that imports and analyzes CSV
score data exported from UDisc — the popular disc golf score tracking app. It
processes player and course data to generate detailed statistics, helping disc
golf enthusiasts gain insights into their gameplay and performance trends.

## Usage

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

### Prepare UDISC CSV files

Use the UDisc app to download the CSV files you want to analyze.

Move the CSV files into a separate directory named e.g., `score_cards`.

### Course Analysis

Plot the course analysis for a specific course by running the
`course_analysis.py` script.

Here is an example use of `course_analysis.py` to plot the averages per hole for
course "Vipan", layout "Main" for all players:

```
python course_analysis.py --csv-dir score_cards --course Vipan --layout Main
```

Here is an example of how that graph can look:

![course-analysis-demo](docs/course-analysis-demo.png)

It is also possible to specify one or more players by using the `-p` or
`--player` option:

```
python course_analysis.py -d score_cards -c Vipan --layout Main -p 'Isak ”Bush Walker” Jacobsson'
```

For more help on how to use the `course_analysis.py` script run the help
command:

```
python course_analysis.py -h
```
