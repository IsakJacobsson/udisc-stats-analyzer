import itertools

import matplotlib.pyplot as plt
import seaborn as sns


def render_distribution_matplotlib(score_counts):
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

    fig, ax = plt.subplots()

    def make_label(pct):
        absolute = int(
            round(
                pct / 100.0
                * score_counts["Count"].sum()
            )
        )
        return f"{pct:.1f}%\n({absolute})"

    ax.pie(
        score_counts["Count"],
        labels=score_counts["ScoreType"],
        autopct=make_label,
        startangle=90,
        textprops={"fontsize": 12},
        colors=colors,
    )

    ax.set_title("Score Distribution")

    return fig


def render_performance_matplotlib(plot_data):
    sns.set_theme(style="ticks", palette="pastel")

    fig, ax = plt.subplots()

    marker_styles = [
        "o", "s", "D", "^", "v", "<", ">",
        "P", "X", "*", "+", "H", "1", "2", "3", "4",
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
            ax=ax,
        )

        if not plot_data["hide_avg"]:
            player_color = line.lines[-1].get_color()

            ax.axhline(
                y=player_data["average"],
                linewidth=0.8,
                alpha=0.8,
                color=player_color,
                linestyle="--",
            )

    if plot_data["par"] is not None:
        ax.axhline(
            y=plot_data["par"],
            label="Par",
            linewidth=2.5,
            alpha=0.8,
            color="green",
            linestyle="--",
        )

    ax.set_xlabel(plot_data["x_axis_label"])
    ax.set_title("Performance Curve")
    ax.legend()

    return fig


def render_hole_distribution_matplotlib(
    plot_data,
    hide_par=False,
):
    sns.set_theme(style="ticks", palette="pastel")

    scores = plot_data["scores"]
    averages = plot_data["averages"]
    par = plot_data["par"]

    holes = sorted(par["Hole"].unique())

    fig, ax = plt.subplots()

    # Box plot
    sns.boxplot(
        x="Hole",
        y="Score",
        data=scores,
        order=holes,
        ax=ax,
    )

    # Individual attempts
    sns.stripplot(
        data=scores,
        x="Hole",
        y="Score",
        order=holes,
        size=4,
        color=".3",
        ax=ax,
    )

    # Average score
    sns.pointplot(
        x="Hole",
        y="AverageScore",
        data=averages,
        order=holes,
        errorbar=None,
        color="red",
        marker="",
        ax=ax,
    )

    # Par
    if not hide_par:
        par_x = [holes.index(hole) for hole in par["Hole"]]
        ax.scatter(
            par_x,
            par["Par"],
            label="Par",
            zorder=5,
            s=100,
            linewidth=2.5,
            facecolors="none",
            edgecolor="green",
            alpha=0.7,
        )

    ax.set_ylim(bottom=0)

    y_max = int(scores["Score"].max()) + 1
    ax.set_yticks(range(0, y_max + 1))

    ax.set_title("Distribution per Hole")
    ax.grid(True)

    return fig
