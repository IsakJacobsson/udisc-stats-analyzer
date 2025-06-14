import argparse
import os
import csv
from datetime import datetime

import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import pandas as pd
import numpy as np

class PlayerRound:
    def __init__(self, player_name, course_name, layout_name, start_date, end_date,
                 total, plus_minus, round_rating, number_of_holes, holes):
        self.player_name = player_name
        self.course_name = course_name
        self.layout_name = layout_name
        self.start_date = start_date
        self.end_date = end_date
        self.total = total
        self.plus_minus = plus_minus
        self.round_rating = round_rating
        self.number_of_holes = number_of_holes
        self.holes = holes  # Score per hole, List: [hole1, hole2, hole3]
    
    def __repr__(self):
        return f"<PlayerRound {self.player_name}, Total: {self.total}>"

def load_player_rounds_from_csv(file_path):
    rounds = []
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            player_name = row['PlayerName']
            course_name = row['CourseName']
            layout_name = row['LayoutName']
            start_date = datetime.strptime(row['StartDate'], '%Y-%m-%d %H%M')
            end_date = datetime.strptime(row['EndDate'], '%Y-%m-%d %H%M')
            total = int(row['Total']) if row['Total'] else None
            plus_minus = int(row['+/-']) if row['+/-'] else None
            round_rating = float(row['RoundRating']) if row['RoundRating'] else None

            number_of_holes = len(row) - 8 # There are 8 feilds before holes
            holes = [int(row[f'Hole{i}']) if int(row[f'Hole{i}']) != 0 else None for i in range(1, number_of_holes+1)]

            round_instance = PlayerRound(
                player_name, course_name, layout_name, start_date, end_date,
                total, plus_minus, round_rating, number_of_holes, holes
            )
            rounds.append(round_instance)
    return rounds

def load_all_csvs_from_folder(folder_path):
    rounds = []
    for filename in os.listdir(folder_path):
        if not filename.lower().endswith(".csv"):
            continue
        file_path = os.path.join(folder_path, filename)
        rounds.extend(load_player_rounds_from_csv(file_path))
    return rounds

def graph_average(rounds, course_name, layout_name, player_name='all'):
    par_line = []
    lines = []
    for round in rounds:
        if round.course_name != course_name or round.layout_name != layout_name:
            continue
        if round.player_name == 'Par':
            par_line = round.holes
            continue
        if player_name != 'all' and round.player_name != player_name:
            continue
        for i, score in enumerate(round.holes):
            if score is not None:
                lines.append({
                    "Hole": i + 1,
                    "Score": score,
                    "Player": round.player_name
                })

    if not par_line:
        print("Par line not found")
        return

    # Create dataframe from player scores
    df = pd.DataFrame(lines)

    # Create DataFrame for par values
    par_df = pd.DataFrame({
        "Hole": list(range(len(par_line))),
        "Score": par_line,
        "Player": ["Par"] * len(par_line)
    })

    sns.set_theme(style="ticks", palette="pastel")

    # Plot score
    sns.boxplot(x="Hole", y="Score", data=df, order=list(range(1, len(par_line)+1)))

    # Plot all individual attempts
    sns.stripplot(data=df, x="Hole", y="Score", size=4, color=".3")
    
    # Plot par
    sns.scatterplot(x="Hole", y="Score", data=par_df, label="Par", zorder=5, s=100, linewidth=1.5, facecolors='none', edgecolor="dimgray")

    plt.ylim(bottom=0)
    plt.title(f"Boxplot for {course_name}, {layout_name}, player: {player_name}")
    plt.grid(True)
    plt.show()

def main(args):
    rounds = load_all_csvs_from_folder(args.csv_dir)
    graph_average(rounds, args.course, args.layout, args.player)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="UDisc CSV Stats Analyzer — Plot average per hole for course and player"
    )
    parser.add_argument(
        "-d", "--csv-dir",
        type=str,
        required=True,
        help="Path to the directory containing UDisc CSV files"
    )
    parser.add_argument(
        "-c", "--course",
        type=str,
        required=True,
        help="Course name to filter by"
    )
    parser.add_argument(
        "-l", "--layout",
        type=str,
        required=True,
        help="Layout name to filter by"
    )
    parser.add_argument(
        "-u", "--player",
        type=str,
        required=False,
        default="all",
        help="Player name to filter by (default: all)"
    )

    args = parser.parse_args()
    main(args)
