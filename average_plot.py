import os
import csv
from datetime import datetime

import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

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
            holes = [int(row[f'Hole{i}']) for i in range(1, number_of_holes+1)]

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
        if round.player_name == 'Par':
            par_line = round.holes
            continue
        if player_name != 'all' and round.player_name != player_name:
            continue
        if round.course_name != course_name or round.layout_name != layout_name:
            continue
        lines.append(round.holes)

    average_line = []
    for hole in range(len(par_line)):
        sum_for_hole = 0
        nbr_lines = 0
        for line in lines:
            if line[hole] != 0:
                sum_for_hole += line[hole]
                nbr_lines += 1
        average_line.append(sum_for_hole/nbr_lines)

    # Convert to a DataFrame with a "line" label:
    df = pd.DataFrame({
        "x": [i + 1 for i in range(len(par_line))] * 2,
        "y": par_line + average_line,
        "Score": ["Par"] * len(par_line) + [f"Average {player_name}"] * len(average_line)
    })

    # Plot points only (scatter plot)
    sns.scatterplot(data=df, x="x", y="y", hue="Score", s=100)  # s=100 makes points bigger

    # Add labels to each point
    for _, row in df.iterrows():
        plt.text(row["x"], row["y"], f'{row["y"]:.2f}', 
             fontsize=10, ha='right', va='bottom')

    plt.ylim(bottom=0)
    plt.title(f"Average per hole for {course_name}, {layout_name}")
    plt.show()


rounds = load_all_csvs_from_folder("score_cards")
graph_average(rounds, "Vipan", "Main")