import argparse
import glob
import os

import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

def generate_dataframe_per_round(csv_dir):
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

def graph_performance(df, par_df, course_name, layout_name, players, stat, output_path, plot_par):
    sns.set_theme(style="ticks", palette="pastel")

    if players[0] == "All":
        players = list(df["PlayerName"].unique())

    for player in players:
        player_df = df[df["PlayerName"] == player]

        # Plot stat for player
        sns.lineplot(data=player_df, x="StartDate", y=stat, label=player, marker='o', alpha=0.8)
    
    if plot_par:
        plt.axhline(y=par_df.loc[0, stat], label='Par', linewidth=2.5, alpha=0.8, color="green", linestyle="--")
    
    plt.title(f"Performance over time for {stat} on {course_name}, {layout_name}")
    plt.grid(True)
    if output_path:
        plt.savefig(output_path, dpi=100)
    plt.show()

def main(args, players):
    df, par_df = generate_dataframe_per_round(args.csv_dir)
    
    df = filter_df(df, args.course, args.layout, players=players, stat=args.stat)

    par_df = filter_df(par_df, args.course, args.layout, stat=args.stat)

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
    players = args.player if args.player is not None else ["All"]
    main(args, players)
