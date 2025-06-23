import argparse
import glob
import os

import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

def generate_dataframes(csv_dir):
    # Load all CSV files from a directory
    csv_files = glob.glob(os.path.join(csv_dir, "*.csv"))

    result_df = pd.DataFrame()
    result_par_df = pd.DataFrame()

    for file in csv_files:
        df = pd.read_csv(file)

        # Normalize smart quotes in all string columns (e.g., PlayerName)
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].str.replace('[“”]', '"', regex=True)
        
        # Set type for StartDate and EndDate
        df["StartDate"] = pd.to_datetime(df["StartDate"])
        df["EndDate"] = pd.to_datetime(df["EndDate"])

        # Set Total to zero if the round wasn't completed
        holes = [col for col in df.columns if col.startswith("Hole")]
        for index, row in df.iterrows():
            round_finished = True
            for hole in holes:
                if row[hole] == 0:
                    round_finished = False
                    break
            if  not round_finished:
                df.at[index, "Total"] = 0
    
        # Concat to result_par_df
        par_df = df[df["PlayerName"] == "Par"].copy()
        par_df = par_df.drop(columns=["StartDate", "EndDate"])
        result_par_df = pd.concat([result_par_df, par_df], ignore_index=True)
        
        # Conat to result_df
        df = df[df["PlayerName"] != "Par"]
        result_df = pd.concat([result_df, df], ignore_index=True)

    # No need for multiple rows of the same course and layout
    result_par_df = result_par_df.drop_duplicates()

    return result_df, result_par_df

def filter_df_by_players(df, players):
    return df[df['PlayerName'].isin(players)]

def filter_df(df, course_name, layout_name):
    if course_name and layout_name:
        # Filter the DataFrame
        df = df[
            (df["CourseName"] == course_name) &
            (df["LayoutName"] == layout_name)
        ]

    return df

def filter_df(df, course_name, layout_name, players=None, stat=None):
    if course_name:
        df = df[df["CourseName"] == course_name]
    
    if layout_name:
        df = df[df["LayoutName"] == layout_name]
    
    if players and players[0] != "all":
        return df[df['PlayerName'].isin(players)]
    
    if stat and stat in df.columns:
        df = df[df[stat] != 0]
    
    return df

def distribution_dataframe(df, par_df):
    distribution_df = pd.DataFrame(columns=[
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

    hole_cols = [col for col in df.columns if col.startswith("Hole")]

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

        par_row = par_df[(par_df["CourseName"] == row["CourseName"]) & (par_df["LayoutName"] == row["LayoutName"])]

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
        
        distribution_df.loc[len(distribution_df)] = {
            "PlayerName": row["PlayerName"],
            **scores
        }

    return distribution_df

def piechart(df, players, course_name, layout_name, output_path):
    # Filter the DataFrame
    if not course_name:
        course_name = "All"
    if  not layout_name:
        layout_name = "All"

    # Group by PlayerName and sum all other numeric columns
    df = df.groupby("PlayerName", as_index=False).sum()

    if df.empty:
        print(f"No data found for players: {players}'")
        return

    sns.set_theme(style="ticks", palette="pastel")

    score_columns = df.columns.drop("PlayerName")
    scores_sum = df[score_columns].sum()
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
    df, par_df = generate_dataframes(args.csv_dir)

    df = filter_df(df, args.course, args.layout, players)
    df = distribution_dataframe(df, par_df)

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
    if args.course and not args.layout:
        print("Error: c/--course requires --l/--layout to be specified.")
        exit()
    players = args.player if args.player is not None else ["all"]
    main(args, players)
