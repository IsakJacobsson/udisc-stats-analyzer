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

        
        df_fixed = df[df["PlayerName"] != "Par"]

        df_fixed["Total"] = pd.to_numeric(df_fixed["Total"], errors="coerce")

        nbr_holes = len([col for col in df.columns if col.startswith("Hole")])
        for hole in range(1, nbr_holes+1):
            df_fixed[f"Hole{hole}"] = pd.to_numeric(df_fixed[f"Hole{hole}"], errors="coerce")
        
        for index, row in df_fixed.iterrows():
            round_finished = True
            for hole in range(1, nbr_holes+1):
                if row[f"Hole{hole}"] == 0:
                    round_finished = False
                    break
            if  not round_finished:
                df_fixed.at[index, "Total"] = 0

        df_fixed["StartDate"] = pd.to_datetime(df_fixed["StartDate"])
        
        dfs.append(df_fixed)

    # Combine all df_long DataFrames
    df = pd.concat(dfs, ignore_index=True)

    return df

def graph_performance(df, course_name, layout_name, players, stat, output_path):
    # Filter the DataFrame
    subset = df[
        (df["CourseName"] == course_name) &
        (df["LayoutName"] == layout_name)
    ].copy()

    subset = subset[subset[stat] != 0]

    if subset.empty:
        print(f"No data found for Course: '{course_name}', Layout: '{layout_name}'")
        return

    sns.set_theme(style="ticks", palette="pastel")

    if players[0] == "all":
        players = list(subset["PlayerName"].unique())

    for name in players:
        sub_subset = subset[subset["PlayerName"] == name]

        if subset.empty:
            print(f"No data found for player '{name}'")
            continue

        # Plot stat for player
        sns.lineplot(data=sub_subset, x="StartDate", y=stat, label=name, marker='o', alpha=0.8)
    
    plt.title(f"Performance over time for {stat} on {course_name}, {layout_name}")
    plt.grid(True)

    if output_path:
        plt.savefig(output_path, dpi=100)
    plt.show()

def main(args, players):
    df = generate_dataframe(args.csv_dir)
    graph_performance(df, args.course, args.layout, players, args.stat, args.output)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=("UDisc CSV Stats Analyzer — Plot course analysis\n\n"
        "Example usage:\n"
        "    python script.py -d score_cards -c Vipan -l Main\n"
        "    python script.py -d score_cards -c Vipan -l Main -p 'Isak \"Bush Walker\" Jacobsson'\n"
        "    python script.py -d score_cards -c Vipan -l Main -p 'Isak \"Bush Walker\" Jacobsson' -p Johanna\n"
        "    python script.py -d score_cards -c Vipan -l Main -o output_file.png\n"
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
        help="Players to plot stat for"
    )
    parser.add_argument(
        "-s", "--stat",
        type=str,
        default="Total",
        help="What stat to plot, e.g., Total, Hole1, Hole18"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Path to save the plot image (e.g., 'plot.png'). If not provided, the plot is only shown."
    )

    args = parser.parse_args()
    players = args.player if args.player is not None else ["all"]
    main(args, players)
