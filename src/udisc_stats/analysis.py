import numpy as np
import pandas as pd


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

