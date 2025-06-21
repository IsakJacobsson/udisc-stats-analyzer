import argparse
import glob
import os

import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

def generate_dataframe(csv_dir):
    # Load all CSV files from a directory
    csv_files = glob.glob(os.path.join(csv_dir, "*.csv"))

    dfs = []

    for file in csv_files:
        df = pd.read_csv(file)

        # Normalize smart quotes in all string columns (e.g., PlayerName)
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].str.replace('[“”]', '"', regex=True)

        hole_cols = [col for col in df.columns if col.startswith("Hole")]

        # Convert them to integers
        df[hole_cols] = df[hole_cols].astype(int)

        # Extract par row
        par_row = df[df["PlayerName"] == "Par"]

        # Skip "Par" row
        df = df[df["PlayerName"] != "Par"]

        file_df = pd.DataFrame(columns=[
            "PlayerName",
            "CourseName",
            "LayoutName",
            "StartDate",
            "EndDate",
            "Worse than triple bogey",
            "Triple Bogey",
            "Double Bogey",
            "Bogey",
            "Par",
            "Birdie",
            "Eagle",
            "Albatross",
            "Condor",
            "Hole-in-one"
        ])

        for _, row in df.iterrows():
            scores = {
                "Worse than triple bogey": 0,
                "Triple Bogey": 0,
                "Double Bogey": 0,
                "Bogey": 0,
                "Par": 0,
                "Birdie": 0,
                "Eagle": 0,
                "Albatross": 0,
                "Condor": 0,
                "Hole-in-one": 0
            }
            for hole in hole_cols:
                if row[hole] == 1:
                    scores["Hole-in-one"] += 1
                    continue
                if row[hole] == 0:
                    continue
                relative_score = row[hole] - par_row[hole].values[0]
                match relative_score:
                    case -4:
                        scores["Condor"] += 1
                    case -3:
                        scores["Albatross"] += 1
                    case -2:
                        scores["Eagle"] += 1
                    case -1:
                        scores["Birdie"] += 1
                    case 0:
                        scores["Par"] += 1
                    case 1:
                        scores["Bogey"] += 1
                    case 2:
                        scores["Double Bogey"] += 1
                    case 3:
                        scores["Triple Bogey"] += 1
                    case x if x > 3:
                        scores["Worse than triple bogey"] += 1
            
            file_df.loc[len(file_df)] = {
                "PlayerName": row["PlayerName"],
                "CourseName": row["CourseName"],
                "LayoutName": row["LayoutName"],
                "StartDate": row["StartDate"],
                "EndDate": row["EndDate"],
                **scores
            }

        dfs.append(file_df)

    # Combine all df_long DataFrames
    df = pd.concat(dfs, ignore_index=True)

    return df

def piechart(df, players, course_name, layout_name, output_path):

    df_copy = df.copy()
    if players[0] != 'all':
        df_copy = df_copy[df_copy["PlayerName"].isin(players)]
    
    # Filter the DataFrame
    if course_name:
        df_copy = df_copy[df_copy["CourseName"] == course_name]
    else: 
        course_name = "All"
    if layout_name:
        df_copy = df_copy[df_copy["LayoutName"] == layout_name]
    else:
        layout_name = "All"

    # Group by PlayerName and sum all other numeric columns
    df_copy = df_copy.groupby("PlayerName", as_index=False).sum()

    if df_copy.empty:
        print(f"No data found for players: {players}'")
        return

    sns.set_theme(style="ticks", palette="pastel")

    # Your DataFrame is df_copy
    score_columns = df_copy.columns.drop(["PlayerName", "CourseName", "LayoutName", "StartDate", "EndDate"])
    scores_sum = df_copy[score_columns].sum()
    scores_sum = scores_sum[scores_sum > 0]

    plt.figure(figsize=(8, 8))
    plt.pie(
        scores_sum,
        labels=scores_sum.index,
        autopct="%1.1f%%",
        startangle=90,
        textprops={'fontsize': 12}
    )
    
    plt.title(f"Distribution for course: {course_name}, layout: {layout_name}, player(s): {players}")
    if output_path:
        plt.savefig(output_path, dpi=100)
    plt.show()

def main(args, players):
    df = generate_dataframe(args.csv_dir)
    piechart(df, players, args.course, args.layout, args.output)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=("UDisc CSV Stats Analyzer — Distribution plot\n\n"
        "Example usage:\n"
        "    python course_analysis.py -d score_cards\n"
        "    python course_analysis.py -d score_cards -c Vipan\n"
        "    python course_analysis.py -d score_cards -c Vipan -l Main\n"
        "    python course_analysis.py -d score_cards -p 'Isak \"Bush Walker\" Jacobsson'\n"
        "    python course_analysis.py -d score_cards -p 'Isak \"Bush Walker\" Jacobsson' -p Johanna\n"
        "    python course_analysis.py -d score_cards -o output_file.png\n"
        ),
        formatter_class=argparse.RawTextHelpFormatter
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
        help="Course name to filter by"
    )
    parser.add_argument(
        "-l", "--layout",
        type=str,
        help="Layout name to filter by"
    )
    parser.add_argument(
        "-p", "--player",
        action="append",
        default=None,
        help="Player name(s) to filter by (can be used multiple times, e.g., -u Alice -u Bob). Will default to 'all'"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Path to save the plot image (e.g., 'plot.png'). If not provided, the plot is only shown."
    )

    args = parser.parse_args()
    if args.layout and not args.course:
        print("Error: -l/--layout requires -c/--course to be specified.")
        exit()
    players = args.player if args.player is not None else ["all"]
    main(args, players)
