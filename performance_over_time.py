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
        par_df = df[df["PlayerName"] == "Par"]

        if not par_df.empty:
            # Melt par row
            par_df["Total"] = pd.to_numeric(par_df["Total"], errors="coerce")

            nbr_holes = len([col for col in par_df.columns if col.startswith("Hole")])
            for hole in range(1, nbr_holes+1):
                par_df[f"Hole{hole}"] = pd.to_numeric(par_df[f"Hole{hole}"], errors="coerce")
            
            par_df["StartDate"] = pd.to_datetime(par_df["StartDate"])

            par_dfs.append(par_df)

        
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
    par_df = pd.concat(par_dfs, ignore_index=True)

    return df, par_df

def graph_performance(df, par_df, course_name, layout_name, players, stat, output_path, plot_par):
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

    if players[0] != "all":
        subset = subset[subset['PlayerName'].isin(players)]
    else:
        players = list(subset["PlayerName"].unique())

    for name in players:
        sub_subset = subset[subset["PlayerName"] == name]

        if subset.empty:
            print(f"No data found for player '{name}'")
            continue

        # Plot stat for player
        sns.lineplot(data=sub_subset, x="StartDate", y=stat, label=name, marker='o', alpha=0.8)
    
    if plot_par:
        par_subset = par_df[
            (par_df["CourseName"] == course_name) &
            (par_df["LayoutName"] == layout_name)
        ].copy()

        par_subset = par_subset[par_subset['StartDate'].isin(subset['StartDate'])]
        
        sns.lineplot(data=par_subset, x="StartDate", y=stat, label="Par", linewidth=2.5, alpha=0.8, color="green", linestyle="--")
    
    plt.title(f"Performance over time for {stat} on {course_name}, {layout_name}")
    plt.grid(True)

    if output_path:
        plt.savefig(output_path, dpi=100)
    plt.show()

def main(args, players):
    df, par_df = generate_dataframe(args.csv_dir)
    graph_performance(df, par_df, args.course, args.layout, players, args.stat, args.output, args.plot_par)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=("UDisc CSV Stats Analyzer — Plot course analysis\n\n"
        "Example usage:\n"
        "    python performance_over_time.py -d score_cards -c Vipan -l Main\n"
        "    python performance_over_time.py -d score_cards -c Vipan -l Main -s Hole1 \n"
        "    python performance_over_time.py -d score_cards -c Vipan -l Main -p 'Isak \"Bush Walker\" Jacobsson'\n"
        "    python performance_over_time.py -d score_cards -c Vipan -l Main -p 'Isak \"Bush Walker\" Jacobsson' -p Johanna\n"
        "    python performance_over_time.py -d score_cards -c Vipan -l Main -o output_file.png\n"
        "    python performance_over_time.py -d score_cards -c Vipan -l Main -r\n"
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
    parser.add_argument(
        "-r", "--plot-par",
        action="store_true",
        help="Include par line in plot"
    )

    args = parser.parse_args()
    players = args.player if args.player is not None else ["all"]
    main(args, players)
