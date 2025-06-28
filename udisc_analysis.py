import argparse
import glob
import os

import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

def load_and_format_csv(file):
    df = pd.read_csv(file)

    # Normalize smart quotes in all string columns (e.g., PlayerName)
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].str.replace('[“”]', '"', regex=True)

    # Set type for StartDate and EndDate
    df["StartDate"] = pd.to_datetime(df["StartDate"])
    df["EndDate"] = pd.to_datetime(df["EndDate"])
    return df

def generate_dataframe(csv_dir, mode="hole"):
    # Load all CSV files from a directory
    csv_files = glob.glob(os.path.join(csv_dir, "*.csv"))

    result_df, result_par_df = pd.DataFrame(), pd.DataFrame()

    for file in csv_files:
        df = load_and_format_csv(file)
        hole_cols = [col for col in df.columns if col.startswith("Hole")]

        if mode == "hole":
            # Melt hole columns: 'Hole' and 'Strokes'
            df = df.melt(
                id_vars=["PlayerName", "CourseName", "LayoutName", "StartDate", "EndDate"],
                value_vars=hole_cols,
                var_name="Hole",
                value_name="Score"
            )

            # Extract hole number from "Hole1", "Hole2", ..
            df["Hole"] = df["Hole"].str.extract("(\d+)").astype(int)

            # Filter out 0 or NaN scores (unfinished holes)
            df = df[df["Score"] > 0]
        elif mode == "round":
            for index, row in df.iterrows():
                round_finished = True
                for hole in hole_cols:
                    if row[hole] == 0:
                        round_finished = False
                        break
                if  not round_finished:
                    df.at[index, "Total"] = 0
        else:
            print("mode must be one of 'hole' or 'round'.")
            exit()
        
        # Create par and player df
        par_df = df[df["PlayerName"] == "Par"].drop(columns=["StartDate", "EndDate"])
        df = df[df["PlayerName"] != "Par"]

        # Concat dfs into result dfs
        result_df = pd.concat([result_df, df], ignore_index=True)
        result_par_df = pd.concat([result_par_df, par_df], ignore_index=True)

    # No need for multiple rows of the same course and layout
    result_par_df = result_par_df.drop_duplicates()

    return result_df, result_par_df

def convert_to_score_distribution(df, par_df):
    distribution = []

    score_type_map = {
        -4: "Condor",
        -3: "Albatross",
        -2: "Eagle",
        -1: "Birdie",
        0: "Par",
        1: "Bogey",
        2: "Double Bogey",
        3: "Triple Bogey"
    }

    for _, row in df.iterrows():
        score_type = ""
        if row["Score"] == 1:
            score_type = "Hole-in-one"
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
        score_type = score_type_map.get(relative_score, "Worse than triple bogey")
        distribution.append({"ScoreType": score_type})

    return pd.DataFrame(distribution)

def filter_df(df, course_name, layout_name, players=None, stat=None):
    if course_name != "All":
        df = df[df["CourseName"] == course_name]
    
    if layout_name != "All":
        df = df[df["LayoutName"] == layout_name]
    
    if players and players[0] != "All":
        return df[df['PlayerName'].isin(players)]
    
    if stat:
        df = df[df[stat] != 0]
    
    return df

def plot_distribution(df, players, course_name, layout_name, output_path):
    score_counts = df["ScoreType"].value_counts()

    # Define the desired order
    custom_order = ["Worse than triple bogey", "Triple Bogey", "Double Bogey", "Bogey", "Par", "Birdie", "Eagle", "Albatros", "Condor", "Hole-in-one"]

    # Reindex with custom order and drop missing ones
    score_counts = score_counts.reindex(custom_order).dropna()

    sns.set_theme(palette="pastel")

    # Custom colors based on score quality
    color_map = {
        "Worse than triple bogey": "#8B0000",  # dark red
        "Triple Bogey": "#B22222",             # firebrick
        "Double Bogey": "#DC143C",             # crimson
        "Bogey": "#FF6347",                    # tomato
        "Par": "#32CD32",                      # lime green
        "Birdie": "#7CFC00",                   # lawn green
        "Eagle": "#228B22",                    # forest green
        "Albatros": "#00CED1",                 # dark turquoise
        "Condor": "#1E90FF",                   # dodger blue
        "Hole-in-one": "#9370DB"               # medium purple
    }

    colors = [color_map[label] for label in score_counts.index]

    # Show raw counts in the pie chart
    def make_label(pct, all_vals):
        absolute = int(round(pct/100.*sum(all_vals)))
        return f"{pct:.1f}%\n({absolute})"
    
    labels = [f"{label}" for label in score_counts.index]
    autopct = lambda pct: make_label(pct, score_counts)

    plt.pie(
        score_counts,
        labels=labels,
        autopct=autopct,
        startangle=90,
        textprops={'fontsize': 12},
        colors=colors
    )
    
    plt.title(f"Distribution for course: {course_name}, layout: {layout_name}, player(s): {players}")
    if output_path:
        plt.savefig(output_path, dpi=100)
    plt.show()

def plot_performance(df, par_df, course_name, layout_name, players, stat, output_path, plot_par):
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

def plot_hole_distribution(df, par_df, course_name, layout_name, players, output_path, plot_par):
    sns.set_theme(style="ticks", palette="pastel")

    # Plot score
    sns.boxplot(x="Hole", y="Score", data=df, order=list(range(0, len(par_df)+1)))

    # Plot all individual attempts
    sns.stripplot(data=df, x="Hole", y="Score", size=4, color=".3")
    
    # Plot par
    if plot_par:
        sns.scatterplot(x="Hole", y="Score", data=par_df, label="Par", zorder=5, s=100, linewidth=2.5, facecolors='none', edgecolor="green", alpha=0.7)

    plt.ylim(bottom=0)
    y_max = int(df["Score"].max()) + 1
    plt.yticks(list(range(0, y_max + 1)))
    plt.title(f"Boxplot for {course_name}, {layout_name}, player(s): {players}")
    plt.grid(True)

    if output_path:
        plt.savefig(output_path, dpi=100)
    plt.show()

def print_basic_stats(df):
    print("----- Basic overview -----")
    num_rounds = len(df[['PlayerName', 'StartDate']].drop_duplicates())
    print(f"Rounds: {num_rounds}")
    print(f"Holes: {len(df)}")
    print(f"Throws: {df['Score'].sum()}")

def score_distribution(args):
    df, par_df = generate_dataframe(args.csv_dir)

    df = filter_df(df, args.course, args.layout, args.players)
    df = convert_to_score_distribution(df, par_df)

    plot_distribution(df, args.players, args.course, args.layout, args.output)

def performance_over_time(args):
    df, par_df = generate_dataframe(args.csv_dir, mode="round")
    
    df = filter_df(df, args.course, args.layout, players=args.players, stat=args.stat)
    par_df = filter_df(par_df, args.course, args.layout, stat=args.stat)

    plot_performance(df, par_df, args.course, args.layout, args.players, args.stat, args.output, args.plot_par)

def hole_distribution(args):
    df, par_df = generate_dataframe(args.csv_dir)

    df = filter_df(df, args.course, args.layout, players=args.players)
    par_df = filter_df(par_df, args.course, args.layout)

    plot_hole_distribution(df, par_df, args.course, args.layout, args.players, args.output, args.plot_par)

def basic_stats(args):
    df, _ = generate_dataframe(args.csv_dir)

    df = filter_df(df, args.course, args.layout, players=args.players)

    print_basic_stats(df)

def main():
    parser = argparse.ArgumentParser(description="UDisc CSV Stats Analyzer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Score distribution subparser
    parser_score = subparsers.add_parser("score-distribution", help="Plot score type distribution")
    parser_score.add_argument(
        "-d", "--csv-dir",
        type=str,
        required=True,
        help="Path to the directory containing UDisc CSV files"
    )
    parser_score.add_argument(
        "-c", "--course",
        type=str,
        default="All",
        help="Course name to filter by. Will default to 'All'."
    )
    parser_score.add_argument(
        "-l", "--layout",
        type=str,
        default="All",
        help="Layout name to filter by. Will default to 'All'."
    )
    parser_score.add_argument(
        "-p", "--player",
        action="append",
        default=None,
        help="Player name(s) to filter by (can be used multiple times, e.g., -p Alice -p Bob). Will default to 'All'"
    )
    parser_score.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Path to save the plot image (e.g., 'plot.png'). If not provided, the plot is only shown."
    )

    # Performance over time subparser
    parser_perf = subparsers.add_parser("performance-over-time", help="Plot performance over time")
    parser_perf.add_argument(
        "-d", "--csv-dir",
        type=str,
        required=True,
        help="Path to the directory containing UDisc CSV files"
    )
    parser_perf.add_argument(
        "-c", "--course",
        type=str,
        required=True,
        help="Course name to filter by"
    )
    parser_perf.add_argument(
        "-l", "--layout",
        type=str,
        required=True,
        help="Layout name to filter by"
    )
    parser_perf.add_argument(
        "-p", "--player",
        action="append",
        default=None,
        help="Player name(s) to filter by (can be used multiple times, e.g., -p Alice -p Bob). Will default to 'All'"
    )
    parser_perf.add_argument(
        "-s", "--stat",
        type=str,
        default="Total",
        help="What stat to plot, e.g., Total, Hole1, Hole18"
    )
    parser_perf.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Path to save the plot image (e.g., 'plot.png'). If not provided, the plot is only shown."
    )
    parser_perf.add_argument(
        "-r", "--plot-par",
        action="store_true",
        help="Include par line in plot"
    )

    # Hole distribution subparser
    parser_course = subparsers.add_parser("hole-distribution", help="Analyze scores per course")
    parser_course.add_argument(
        "-d", "--csv-dir",
        type=str,
        required=True,
        help="Path to the directory containing UDisc CSV files"
    )
    parser_course.add_argument(
        "-c", "--course",
        type=str,
        required=True,
        help="Course name to filter by"
    )
    parser_course.add_argument(
        "-l", "--layout",
        type=str,
        required=True,
        help="Layout name to filter by"
    )
    parser_course.add_argument(
        "-p", "--player",
        action="append",
        default=None,
        help="Player name(s) to filter by (can be used multiple times, e.g., -p Alice -p Bob). Will default to 'All'"
    )
    parser_course.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Path to save the plot image (e.g., 'plot.png'). If not provided, the plot is only shown."
    )
    parser_course.add_argument(
        "-r", "--plot-par",
        action="store_true",
        help="Include par line in plot"
    )

    # Basic stats subparser
    parser_basic_stats = subparsers.add_parser("basic-stats", help="Get some basic stats")
    parser_basic_stats.add_argument(
        "-d", "--csv-dir",
        type=str,
        required=True,
        help="Path to the directory containing UDisc CSV files"
    )
    parser_basic_stats.add_argument(
        "-c", "--course",
        type=str,
        default="All",
        help="Course name to filter by"
    )
    parser_basic_stats.add_argument(
        "-l", "--layout",
        type=str,
        default="All",
        help="Layout name to filter by"
    )
    parser_basic_stats.add_argument(
        "-p", "--player",
        action="append",
        default=None,
        help="Player name(s) to filter by (can be used multiple times, e.g., -p Alice -p Bob). Will default to 'All'"
    )
    parser_basic_stats.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Path to save the plot image (e.g., 'plot.png'). If not provided, the plot is only shown."
    )
    parser_basic_stats.add_argument(
        "-r", "--plot-par",
        action="store_true",
        help="Include par line in plot"
    )

    args = parser.parse_args()
    
    # Needs to be set to ["All"] if not set
    args.players = args.player if args.player is not None else ["All"]

    if args.command == "score-distribution":
        score_distribution(args)
    elif args.command == "performance-over-time":
        performance_over_time(args)
    elif args.command == "hole-distribution":
        hole_distribution(args)
    elif args.command == "basic-stats":
        basic_stats(args)

if __name__ == "__main__":
    main()