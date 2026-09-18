import argparse
from enum import Enum

import pandas as pd

from .analysis import (
    get_basic_stats,
    get_hole_distribution,
    get_distribution,
    get_performance_curve,
)
from .data import filter_df, generate_dataframe
from .plotting import (
    render_distribution_matplotlib,
    render_hole_distribution_matplotlib,
    render_performance_matplotlib,
)


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


def score_distribution(args):
    score_counts = get_distribution(
        csv_dir=args.csv_dir,
        course=args.course,
        layout=args.layout,
        players=args.players,
        after=args.after,
        before=args.before,
    )

    render_distribution_matplotlib(score_counts, args.output)


def performance_curve(args):
    plot_data = get_performance_curve(
        csv_dir=args.csv_dir,
        course=args.course,
        layout=args.layout,
        players=args.players,
        after=args.after,
        before=args.before,
        stat=args.stat,
        hide_par=args.hide_par,
        x_axis_mode=args.x_axis_mode,
        hide_avg=args.hide_avg,
        smoothness=args.smoothness,
    )

    render_performance_matplotlib(
        plot_data,
        args.output,
    )


def hole_distribution(args):
    plot_data = get_hole_distribution(
        csv_dir=args.csv_dir,
        course=args.course,
        layout=args.layout,
        players=args.players,
        after=args.after,
        before=args.before,
    )

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

    output_text = get_basic_stats(df_holes, df_rounds)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output_text + "\n")
    else:
        print(output_text)


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
            dest="players",
            action="append",
            default=["All"],
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

    command_handlers = {
        "score-distribution": score_distribution,
        "performance-curve": performance_curve,
        "hole-distribution": hole_distribution,
        "basic-stats": basic_stats,
    }

    command_handlers[args.command](args)

