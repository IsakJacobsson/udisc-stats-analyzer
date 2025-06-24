import argparse
import glob
import os

import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

def generate_dataframe_per_hole(csv_dir):
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
        
        # Only include hole columns
        hole_cols = [col for col in df.columns if col.startswith("Hole")]

        # Melt hole columns: 'Hole' and 'Strokes'
        df_long = df.melt(
            id_vars=["PlayerName", "CourseName", "LayoutName", "StartDate", "EndDate"],
            value_vars=hole_cols,
            var_name="Hole",
            value_name="Score"
        )

        # Extract hole number from "Hole1", "Hole2", ..
        df_long["Hole"] = df_long["Hole"].str.extract("(\d+)").astype(int)

        # Filter out 0 or NaN scores (unfinished holes)
        df_long = df_long[df_long["Score"] > 0]
        
        # Concat to result_par_df
        par_df = df_long[df_long["PlayerName"] == "Par"].copy()
        par_df = par_df.drop(columns=["StartDate", "EndDate"])
        result_par_df = pd.concat([result_par_df, par_df], ignore_index=True)
        
        # Conat to result_df
        df_long = df_long[df_long["PlayerName"] != "Par"]
        result_df = pd.concat([result_df, df_long], ignore_index=True)

    # No need for multiple rows of the same course and layout
    result_par_df = result_par_df.drop_duplicates()

    return result_df, result_par_df

def filter_df(df, course_name, layout_name, players=None, stat=None):
    if course_name != "All":
        df = df[df["CourseName"] == course_name]
    
    if layout_name != "All":
        df = df[df["LayoutName"] == layout_name]
    
    if players and players[0] != "All":
        return df[df['PlayerName'].isin(players)]
    
    if stat and stat in df.columns:
        df = df[df[stat] != 0]
    
    return df

def convert_to_score_distribution(df, par_df):
    distribution_df = pd.DataFrame(columns=["ScoreType"])

    for _, row in df.iterrows():
        scoreType = ""
        if row["Score"] == 1:
            scoreType = "Hole-in-one"
            continue
        if row["Score"] == 0:
            # Skip this value
            continue
        par_score = par_df[
            (par_df["CourseName"] == row["CourseName"]) &
            (par_df["LayoutName"] == row["LayoutName"]) &
            (par_df["Hole"] == row["Hole"])
        ]["Score"].values[0]
        relative_score = row["Score"] - par_score
        match relative_score:
            case -4:
                scoreType = "Condor"
            case -3:
                scoreType = "Albatross"
            case -2:
                scoreType = "Eagle"
            case -1:
                scoreType = "Birdie"
            case 0:
                scoreType = "Par"
            case 1:
                scoreType = "Bogey"
            case 2:
                scoreType = "Double Bogey"
            case 3:
                scoreType = "Triple Bogey"
            case x if x > 3:
                "Worse than triple bogey"
        
        distribution_df.loc[len(distribution_df)] = {
            "ScoreType": scoreType
        }

    return distribution_df

def piechart(df, players, course_name, layout_name, output_path):

    score_counts = df["ScoreType"].value_counts()

    # Define the desired order
    custom_order = ["Worse than triple bogey", "Triple Bogey", "Double Bogey", "Bogey", "Par", "Birdie", "Eagle", "Albatros", "Condor", "Hole-in-one"]

    # Reindex with custom order and drop missing ones
    score_counts = score_counts.reindex(custom_order).dropna()

    sns.set_theme(palette="pastel")

    plt.pie(
        score_counts,
        labels=score_counts.index,
        autopct="%1.1f%%",
        startangle=90,
        textprops={'fontsize': 12}
    )
    
    plt.title(f"Distribution for course: {course_name}, layout: {layout_name}, player(s): {players}")
    if output_path:
        plt.savefig(output_path, dpi=100)
    plt.show()

def main(args, players):
    df, par_df = generate_dataframe_per_hole(args.csv_dir)

    df = filter_df(df, args.course, args.layout, players)
    df = convert_to_score_distribution(df, par_df)

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
        default="All",
        help="Course name to filter by"
    )
    parser.add_argument(
        "-l", "--layout",
        type=str,
        default="All",
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
    players = args.player if args.player is not None else ["All"]
    main(args, players)
