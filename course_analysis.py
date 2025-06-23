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

def graph_average(df, par_df, course_name, layout_name, players, output_path, plot_par):
    sns.set_theme(style="ticks", palette="pastel")

    # Plot score
    sns.boxplot(x="Hole", y="Score", data=df, order=list(range(0, len(par_df)+1)))

    # Plot all individual attempts
    sns.stripplot(data=df, x="Hole", y="Score", size=4, color=".3")
    
    # Plot par
    if plot_par:
        sns.scatterplot(x="Hole", y="Score", data=par_df, label="Par", zorder=5, s=100, linewidth=2.5, facecolors='none', edgecolor="green", alpha=0.7)

    plt.ylim(bottom=0)
    plt.title(f"Boxplot for {course_name}, {layout_name}, player(s): {players}")
    plt.grid(True)

    if output_path:
        plt.savefig(output_path, dpi=100)
    plt.show()

def main(args, players):
    df, par_df = generate_dataframe_per_hole(args.csv_dir)

    df = filter_df(df, args.course, args.layout)
    if players[0] != "all":
        df = filter_df_by_players(df, players)

    par_df = filter_df(par_df, args.course, args.layout)

    graph_average(df, par_df, args.course, args.layout, players, args.output, args.plot_par)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=("UDisc CSV Stats Analyzer — Plot course analysis\n\n"
        "Example usage:\n"
        "    python course_analysis.py -d score_cards -c Vipan -l Main\n"
        "    python course_analysis.py -d score_cards -c Vipan -l Main -p 'Isak \"Bush Walker\" Jacobsson'\n"
        "    python course_analysis.py -d score_cards -c Vipan -l Main -p 'Isak \"Bush Walker\" Jacobsson' -p Johanna\n"
        "    python course_analysis.py -d score_cards -c Vipan -l Main -o output_file.png\n"
        "    python course_analysis.py -d score_cards -c Vipan -l Main -r\n"
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
    parser.add_argument(
        "-r", "--plot-par",
        action="store_true",
        help="Include par line in plot"
    )

    args = parser.parse_args()
    players = args.player if args.player is not None else ["all"]
    main(args, players)
