import argparse
import itertools
from enum import Enum
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


class Arg(Enum):
    CSV_DIR = 1
    COURSE = 2
    LAYOUT = 3
    PLAYERS = 4
    AFTER = 5
    BEFORE = 6
    OUTPUT = 7
    STAT = 8
    HIDE_PAR = 9
    X_AXIS_MODE = 10
    COURSE_REQUIRED = 11
    LAYOUT_REQUIRED = 12
    HIDE_AVG = 13
    SMOOTHNESS = 14


def valid_date(s):
    try:
        return pd.Timestamp(s)
    except Exception:
        raise argparse.ArgumentTypeError(
            f"Invalid date: '{s}'. Format must be YYYY-MM-DD"
        )


def load_and_format_csv(file):
    df = pd.read_csv(file)

    # Normalize smart quotes in all string columns (e.g., PlayerName)
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].str.replace("[“”]", '"', regex=True)

    # Set type for StartDate and EndDate
    df["StartDate"] = pd.to_datetime(df["StartDate"])
    df["EndDate"] = pd.to_datetime(df["EndDate"])
    return df


def generate_dataframe(csv_dir, mode="hole"):
    # Load all CSV files from a directory
    csv_files = list(Path(csv_dir).glob("*.csv"))

    result_df, result_par_df = pd.DataFrame(), pd.DataFrame()

    for file in csv_files:
        df = load_and_format_csv(file)
        hole_cols = [col for col in df.columns if col.startswith("Hole")]

        if mode == "hole":
            # Melt hole columns: 'Hole' and 'Strokes'
            df = df.melt(
                id_vars=[
                    "PlayerName",
                    "CourseName",
                    "LayoutName",
                    "StartDate",
                    "EndDate",
                ],
                value_vars=hole_cols,
                var_name="Hole",
                value_name="Score",
            )

            # Extract hole number from "Hole1", "Hole2", ..
            df["Hole"] = df["Hole"].str.extract(r"(\d+)").astype(int)

            # Filter out 0 or NaN scores (unfinished holes)
            df = df[df["Score"] > 0]
        elif mode == "round":
            for index, row in df.iterrows():
                round_finished = True
                for hole in hole_cols:
                    if row[hole] == 0:
                        round_finished = False
                        break
                if not round_finished:
                    df.at[index, "Total"] = 0
        else:
            raise ValueError("mode must be one of 'hole' or 'round'")

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
        3: "Triple Bogey",
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
            (par_df["CourseName"] == row["CourseName"])
            & (par_df["LayoutName"] == row["LayoutName"])
            & (par_df["Hole"] == row["Hole"])
        ]["Score"].values[0]
        relative_score = row["Score"] - par_score
        score_type = score_type_map.get(relative_score, "Worse than triple bogey")
        distribution.append({"ScoreType": score_type})

    return pd.DataFrame(distribution)


def filter_df(
    df,
    course_name,
    layout_name,
    after_date=None,
    before_date=None,
    players=None,
    stat=None,
):
    if course_name != "All":
        df = df[df["CourseName"] == course_name]

    if layout_name != "All":
        df = df[df["LayoutName"] == layout_name]

    if after_date:
        df = df[df["StartDate"] >= after_date]

    if before_date:
        df = df[df["StartDate"] <= before_date]

    if players and players[0] != "All":
        df = df[df["PlayerName"].isin(players)]

    if stat:
        # Stats with 0 are not valid because they are not filled in
        df = df[df[stat] != 0]

    return df


def prepare_distribution(df):
    custom_order = [
        "Worse than triple bogey",
        "Triple Bogey",
        "Double Bogey",
        "Bogey",
        "Par",
        "Birdie",
        "Eagle",
        "Albatross",
        "Condor",
        "Hole-in-one",
    ]

    score_counts = (
        df["ScoreType"]
        .value_counts()
        .reindex(custom_order)
        .dropna()
        .rename_axis("ScoreType")
        .reset_index(name="Count")
    )

    return score_counts


def prepare_performance_curve(
    df,
    par_df,
    players,
    stat,
    hide_par,
    x_axis_mode,
    hide_avg,
    smoothness,
):
    if players[0] == "All":
        players = list(df["PlayerName"].unique())

    df = df.copy()

    if x_axis_mode == "round":
        unique_dates = sorted(df["StartDate"].unique())
        date_to_round = {
            date: idx + 1
            for idx, date in enumerate(unique_dates)
        }
        df["RoundIndex"] = df["StartDate"].map(date_to_round)

    x_col = "RoundIndex" if x_axis_mode == "round" else "StartDate"

    players_data = []

    for player in players:
        player_df = df[df["PlayerName"] == player].copy()

        if smoothness > 1:
            player_df[stat] = (
                player_df[stat]
                .rolling(window=smoothness, min_periods=1)
                .mean()
            )

        players_data.append({
            "player": player,
            "data": player_df[[x_col, stat]].copy(),
            "average": player_df[stat].mean(),
        })

    return {
        "players": players_data,
        "x": x_col,
        "stat": stat,
        "par": None if hide_par else par_df.iloc[0][stat],
        "hide_avg": hide_avg,
        "x_axis_label": (
            "Round number"
            if x_axis_mode == "round"
            else "Date"
        ),
    }


def prepare_hole_distribution(df, par_df):
    # Score observations, one row per attempt
    scores = (
        df[["Hole", "Score"]]
        .dropna()
        .copy()
    )

    # Mean score for each hole
    averages = (
        scores
        .groupby("Hole", as_index=False)["Score"]
        .mean()
        .rename(columns={"Score": "AverageScore"})
    )

    # Par score for each hole
    par = (
        par_df[["Hole", "Score"]]
        .dropna()
        .rename(columns={"Score": "Par"})
    )

    return {
        "scores": scores,
        "averages": averages,
        "par": par,
    }


def calculate_basic_stats(df_holes, df_rounds):
    df_rounds = df_rounds.sort_values(by="StartDate")

    df_finished_rounds = df_rounds[df_rounds["Total"] != 0]

    stats = {
        "rounds": len(df_rounds),
        "finished_rounds": len(df_finished_rounds),
        "best_round": df_finished_rounds["Total"].min(),
        "worst_round": df_finished_rounds["Total"].max(),
        "average_total": df_finished_rounds["Total"].mean(),
        "score_change_per_round": 0,
        "holes": len(df_holes),
        "throws": df_holes["Score"].sum(),
        "players": {},
    }

    if len(df_finished_rounds) > 1:
        x = np.arange(len(df_finished_rounds))
        y = df_finished_rounds["Total"].to_numpy()
        stats["score_change_per_round"] = np.polyfit(x, y, deg=1)[0]

    for player in df_rounds["PlayerName"].unique():
        df_rounds_player = df_rounds[
            df_rounds["PlayerName"] == player
        ]
        df_finished_rounds_player = df_finished_rounds[
            df_finished_rounds["PlayerName"] == player
        ]
        df_holes_player = df_holes[
            df_holes["PlayerName"] == player
        ]

        player_stats = {
            "rounds": len(df_rounds_player),
            "finished_rounds": len(df_finished_rounds_player),
            "best_round": df_finished_rounds_player["Total"].min(),
            "worst_round": df_finished_rounds_player["Total"].max(),
            "average_total": df_finished_rounds_player["Total"].mean(),
            "score_change_per_round": 0,
            "holes": len(df_holes_player),
            "throws": df_holes_player["Score"].sum(),
        }

        if len(df_finished_rounds_player) > 1:
            x = np.arange(len(df_finished_rounds_player))
            y = df_finished_rounds_player["Total"].to_numpy()
            player_stats["score_change_per_round"] = np.polyfit(
                x, y, deg=1
            )[0]

        stats["players"][player] = player_stats

    return stats


def format_basic_stats(stats):
    lines = []

    lines.append("----- Basic overview -----")
    lines.append(f"Rounds: {stats['rounds']}")
    lines.append(f"Finished rounds: {stats['finished_rounds']}")
    lines.append(f"Best round: {stats['best_round']}p")
    lines.append(f"Worst round: {stats['worst_round']}p")
    lines.append(f"Average total: {stats['average_total']:.2f}p")
    lines.append(
        f"Score change per round played: "
        f"{stats['score_change_per_round']:.2f}p"
    )
    lines.append(f"Holes: {stats['holes']}")
    lines.append(f"Throws: {stats['throws']}")

    for player, player_stats in stats["players"].items():
        lines.append("")
        lines.append(f"{player}:")
        lines.append(f"    Rounds: {player_stats['rounds']}")
        lines.append(
            f"    Finished rounds: "
            f"{player_stats['finished_rounds']}"
        )
        lines.append(
            f"    Best round: {player_stats['best_round']}p"
        )
        lines.append(
            f"    Worst round: {player_stats['worst_round']}p"
        )
        lines.append(
            f"    Average total: "
            f"{player_stats['average_total']:.2f}p"
        )
        lines.append(
            f"    Score change per round played: "
            f"{player_stats['score_change_per_round']:.2f}p"
        )
        lines.append(f"    Holes: {player_stats['holes']}")
        lines.append(f"    Throws: {player_stats['throws']}")

    return "\n".join(lines)


def render_distribution_matplotlib(score_counts, output_path=None):
    sns.set_theme(palette="pastel")

    color_map = {
        "Worse than triple bogey": "#8B0000",
        "Triple Bogey": "#B22222",
        "Double Bogey": "#DC143C",
        "Bogey": "#FF6347",
        "Par": "#32CD32",
        "Birdie": "#7CFC00",
        "Eagle": "#228B22",
        "Albatross": "#00CED1",
        "Condor": "#1E90FF",
        "Hole-in-one": "#9370DB",
    }

    colors = [
        color_map[label]
        for label in score_counts["ScoreType"]
    ]

    def make_label(pct):
        absolute = int(
            round(
                pct / 100.0
                * score_counts["Count"].sum()
            )
        )
        return f"{pct:.1f}%\n({absolute})"

    plt.pie(
        score_counts["Count"],
        labels=score_counts["ScoreType"],
        autopct=make_label,
        startangle=90,
        textprops={"fontsize": 12},
        colors=colors,
    )

    plt.title("Score Distribution")

    if output_path:
        plt.savefig(output_path, dpi=100)
    else:
        plt.show()


def render_performance_matplotlib(plot_data, output_path=None):
    sns.set_theme(style="ticks", palette="pastel")

    marker_styles = [
        "o", "s", "D", "^", "v", "<", ">",
        "P", "X", "*", "+", "H", "1", "2", "3", "4"
    ]

    marker_cycle = itertools.cycle(marker_styles)

    for player_data in plot_data["players"]:
        player = player_data["player"]
        data = player_data["data"]
        marker = next(marker_cycle)

        line = sns.lineplot(
            data=data,
            x=plot_data["x"],
            y=plot_data["stat"],
            label=player,
            marker=marker,
            alpha=0.8,
        )

        if not plot_data["hide_avg"]:
            player_color = line.lines[-1].get_color()

            plt.axhline(
                y=player_data["average"],
                linewidth=0.8,
                alpha=0.8,
                color=player_color,
                linestyle="--",
            )

    if plot_data["par"] is not None:
        plt.axhline(
            y=plot_data["par"],
            label="Par",
            linewidth=2.5,
            alpha=0.8,
            color="green",
            linestyle="--",
        )

    plt.xlabel(plot_data["x_axis_label"])
    plt.title("Performance Curve")
    plt.legend()

    if output_path:
        plt.savefig(output_path, dpi=100)
    else:
        plt.show()


def render_hole_distribution_matplotlib(
    plot_data,
    output_path=None,
    hide_par=False,
):
    sns.set_theme(style="ticks", palette="pastel")

    scores = plot_data["scores"]
    averages = plot_data["averages"]
    par = plot_data["par"]

    holes = sorted(scores["Hole"].unique())

    # Box plot
    sns.boxplot(
        x="Hole",
        y="Score",
        data=scores,
        order=holes,
    )

    # Individual attempts
    sns.stripplot(
        data=scores,
        x="Hole",
        y="Score",
        size=4,
        color=".3",
    )

    # Average score
    sns.pointplot(
        x="Hole",
        y="AverageScore",
        data=averages,
        errorbar=None,
        color="red",
        marker="",
    )

    # Par
    if not hide_par:
        sns.scatterplot(
            x="Hole",
            y="Par",
            data=par,
            label="Par",
            zorder=5,
            s=100,
            linewidth=2.5,
            facecolors="none",
            edgecolor="green",
            alpha=0.7,
        )

    plt.ylim(bottom=0)

    y_max = int(scores["Score"].max()) + 1
    plt.yticks(range(0, y_max + 1))

    plt.title("Distribution per Hole")
    plt.grid(True)

    if output_path:
        plt.savefig(output_path, dpi=100)
    else:
        plt.show()


def print_basic_stats(df_holes, df_rounds, output_file):
    stats = calculate_basic_stats(df_holes, df_rounds)
    output_text = format_basic_stats(stats)

    if output_file:
        with open(output_file, "w") as f:
            f.write(output_text + "\n")
    else:
        print(output_text)


def score_distribution(args):
    df, par_df = generate_dataframe(args.csv_dir)

    df = filter_df(df, args.course, args.layout, args.after, args.before, args.players)
    df = convert_to_score_distribution(df, par_df)

    score_counts = prepare_distribution(df)

    render_distribution_matplotlib(score_counts, args.output)


def performance_curve(args):
    df, par_df = generate_dataframe(args.csv_dir, mode="round")

    df = filter_df(
        df,
        args.course,
        args.layout,
        args.after,
        args.before,
        players=args.players,
        stat=args.stat,
    )
    par_df = filter_df(par_df, args.course, args.layout, stat=args.stat)

    plot_data = prepare_performance_curve(
        df,
        par_df,
        args.players,
        args.stat,
        args.hide_par,
        args.x_axis_mode,
        args.hide_avg,
        args.smoothness,
    )

    render_performance_matplotlib(plot_data, args.output)


def hole_distribution(args):
    df, par_df = generate_dataframe(args.csv_dir)

    df = filter_df(
        df, args.course, args.layout, args.after, args.before, players=args.players
    )
    par_df = filter_df(par_df, args.course, args.layout)

    plot_data = prepare_hole_distribution(df, par_df)

    render_hole_distribution_matplotlib(plot_data, args.output, args.hide_par)


def basic_stats(args):
    df_holes, _ = generate_dataframe(args.csv_dir)
    df_rounds, _ = generate_dataframe(args.csv_dir, mode="round")

    df_holes = filter_df(
        df_holes,
        args.course,
        args.layout,
        args.after,
        args.before,
        players=args.players,
    )
    df_rounds = filter_df(
        df_rounds,
        args.course,
        args.layout,
        args.after,
        args.before,
        players=args.players,
    )

    print_basic_stats(df_holes, df_rounds, args.output)


def add_arguments(parser, *args):
    course_required = Arg.COURSE_REQUIRED in args
    layout_required = Arg.LAYOUT_REQUIRED in args

    if Arg.CSV_DIR in args:
        parser.add_argument(
            "-d",
            "--csv-dir",
            type=str,
            required=True,
            help="Path to the directory containing UDisc CSV files.",
        )
    if Arg.COURSE in args:
        parser.add_argument(
            "-c",
            "--course",
            type=str,
            required=course_required,
            default=None if course_required else "All",
            help="Course name to filter by."
            + (" Required." if course_required else " Will default to 'All'."),
        )
    if Arg.LAYOUT in args:
        parser.add_argument(
            "-l",
            "--layout",
            type=str,
            required=layout_required,
            default=None if layout_required else "All",
            help="Layout name to filter by."
            + (" Required." if layout_required else " Will default to 'All'."),
        )
    if Arg.PLAYERS in args:
        parser.add_argument(
            "-p",
            "--player",
            action="append",
            default=None,
            help="Player name(s) to filter by (e.g., -p Alice -p Bob). Defaults to 'All'.",
        )
    if Arg.AFTER in args:
        parser.add_argument(
            "--after",
            type=valid_date,
            default=None,
            help="Only include data after this date (inclusive). Format: YYYY-MM-DD.",
        )
    if Arg.BEFORE in args:
        parser.add_argument(
            "--before",
            type=valid_date,
            default=None,
            help="Only include data before this date (inclusive). Format: YYYY-MM-DD.",
        )
    if Arg.OUTPUT in args:
        parser.add_argument(
            "-o",
            "--output",
            type=str,
            default=None,
            help="Path to save the resulting output to. When set, the result is suppressed.",
        )
    if Arg.STAT in args:
        parser.add_argument(
            "-s",
            "--stat",
            type=str,
            default="Total",
            help="What stat to plot, e.g., Total, Hole1, Hole18.",
        )
    if Arg.HIDE_PAR in args:
        parser.add_argument(
            "--hide-par", action="store_true", help="Hide par reference in plot."
        )
    if Arg.X_AXIS_MODE in args:
        parser.add_argument(
            "--x-axis-mode",
            choices=["round", "date"],
            default="round",
            help="Choose 'date' to plot against actual dates or 'round' to plot by round number.",
        )
    if Arg.HIDE_AVG in args:
        parser.add_argument(
            "--hide-avg", action="store_true", help="Hide average lines in plot."
        )
    if Arg.SMOOTHNESS in args:
        parser.add_argument(
            "--smoothness", type=int, default=1, help="Apply rolling average on plot."
        )
    return parser


def main():
    parser = argparse.ArgumentParser(description="UDisc CSV Stats Analyzer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Score distribution subparser
    parser_score = subparsers.add_parser(
        "score-distribution", help="Plot score type distribution."
    )
    add_arguments(
        parser_score,
        Arg.CSV_DIR,
        Arg.COURSE,
        Arg.LAYOUT,
        Arg.PLAYERS,
        Arg.AFTER,
        Arg.BEFORE,
        Arg.OUTPUT,
    )

    # Performance curve subparser
    parser_perf = subparsers.add_parser(
        "performance-curve", help="Plot performance curve."
    )
    add_arguments(
        parser_perf,
        Arg.CSV_DIR,
        Arg.COURSE,
        Arg.COURSE_REQUIRED,
        Arg.LAYOUT,
        Arg.LAYOUT_REQUIRED,
        Arg.PLAYERS,
        Arg.AFTER,
        Arg.BEFORE,
        Arg.OUTPUT,
        Arg.STAT,
        Arg.HIDE_PAR,
        Arg.X_AXIS_MODE,
        Arg.HIDE_AVG,
        Arg.SMOOTHNESS,
    )

    # Hole distribution subparser
    parser_course = subparsers.add_parser(
        "hole-distribution", help="Analyze scores per course."
    )
    add_arguments(
        parser_course,
        Arg.CSV_DIR,
        Arg.COURSE,
        Arg.COURSE_REQUIRED,
        Arg.LAYOUT,
        Arg.LAYOUT_REQUIRED,
        Arg.PLAYERS,
        Arg.AFTER,
        Arg.BEFORE,
        Arg.OUTPUT,
        Arg.HIDE_PAR,
    )

    # Basic stats subparser
    parser_basic_stats = subparsers.add_parser(
        "basic-stats", help="Get some basic stats."
    )
    add_arguments(
        parser_basic_stats,
        Arg.CSV_DIR,
        Arg.COURSE,
        Arg.LAYOUT,
        Arg.PLAYERS,
        Arg.AFTER,
        Arg.BEFORE,
        Arg.OUTPUT,
    )

    args = parser.parse_args()

    # Needs to be set to ["All"] if not set
    args.players = args.player if args.player is not None else ["All"]

    command_handlers = {
        "score-distribution": score_distribution,
        "performance-curve": performance_curve,
        "hole-distribution": hole_distribution,
        "basic-stats": basic_stats,
    }

    command_handlers[args.command](args)


if __name__ == "__main__":
    main()
