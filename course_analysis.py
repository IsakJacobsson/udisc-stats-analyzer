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
    par_dfs = []

    for file in csv_files:
        df = pd.read_csv(file)

        # Normalize smart quotes in all string columns (e.g., PlayerName)
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].str.replace('[“”]', '"', regex=True)

        # Get par row separately
        par_row = df[df["PlayerName"] == "Par"]

        if not par_row.empty:
            # Melt par row
            hole_cols = [col for col in df.columns if col.startswith("Hole")]
            par_long = par_row.melt(
                id_vars=["CourseName", "LayoutName"],
                value_vars=hole_cols,
                var_name="Hole",
                value_name="Score"
            )
            par_long["Hole"] = par_long["Hole"].str.extract(r"(\d+)").astype(int)
            par_long["Score"] = pd.to_numeric(par_long["Score"], errors="coerce")

            par_dfs.append(par_long)

        # Skip "Par" row
        df = df[df["PlayerName"] != "Par"]
        
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

        # Convert score to numeric, just in case
        df_long["Score"] = pd.to_numeric(df_long["Score"], errors="coerce")

        # Filter out 0 or NaN scores (unfinished holes)
        df_long = df_long[df_long["Score"] > 0]
        
        dfs.append(df_long)

    # Combine all df_long DataFrames
    df = pd.concat(dfs, ignore_index=True)
    par_df = pd.concat(par_dfs, ignore_index=True).drop_duplicates(
        subset=["CourseName", "LayoutName", "Hole"]
    )

    return df, par_df

def graph_average(df, par_df, course_name, layout_name, player_name='all'):
    # Filter the DataFrame
    subset = df[
        (df["CourseName"] == course_name) &
        (df["LayoutName"] == layout_name)
    ].copy()

    if player_name != 'all':
        subset = subset[(subset["PlayerName"] == player_name)]

    subset_par = par_df[
        (par_df["CourseName"] == course_name) &
        (par_df["LayoutName"] == layout_name)
    ].copy()

    # Shift to align scores in graph
    # TODO: figure out why this shift is needed
    subset_par["Hole"] = subset_par["Hole"] - 1

    if subset.empty:
        print(f"No data found for Course: '{course_name}', Layout: '{layout_name}'")
        return

    sns.set_theme(style="ticks", palette="pastel")

    # Plot score
    sns.boxplot(x="Hole", y="Score", data=subset, order=list(range(1, len(subset_par)+1)))

    # Plot all individual attempts
    sns.stripplot(data=subset, x="Hole", y="Score", size=4, color=".3")
    
    # Plot par
    sns.scatterplot(x="Hole", y="Score", data=subset_par, label="Par", zorder=5, s=100, linewidth=2.5, facecolors='none', edgecolor="green", alpha=0.7)

    plt.ylim(bottom=0)
    plt.title(f"Boxplot for {course_name}, {layout_name}, player: {player_name}")
    plt.grid(True)
    plt.show()

def main(args):
    df, par_df = generate_dataframe(args.csv_dir)
    graph_average(df, par_df, args.course, args.layout, args.player)

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
