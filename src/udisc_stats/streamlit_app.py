import streamlit as st
from pathlib import Path

from udisc_stats.analysis import (
    get_basic_stats,
    get_distribution,
    get_hole_distribution,
    get_performance_curve,
)
from udisc_stats.data import generate_dataframe, filter_df
from udisc_stats.plotting import (
    render_distribution_matplotlib,
    render_hole_distribution_matplotlib,
    render_performance_matplotlib,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = PROJECT_ROOT / "score_cards"


st.set_page_config(
    page_title="UDisc Stats Analyzer",
    page_icon="🥏",
    layout="wide",
)


@st.cache_data
def load_data(csv_dir):
    df_holes, _ = generate_dataframe(csv_dir)
    df_rounds, _ = generate_dataframe(csv_dir, mode="round")
    return df_holes, df_rounds


csv_dir = str(DEFAULT_DATA_DIR)


try:
    df_holes, df_rounds = load_data(csv_dir)
except Exception as e:
    st.error(f"Unable to load data: {e}")
    st.stop()


# -------------------------------------------------------------------
# Header
# -------------------------------------------------------------------

st.title("🥏 UDisc Stats Analyzer")

# -------------------------------------------------------------------
# Filter options
# -------------------------------------------------------------------

courses = sorted(
    df_rounds["CourseName"].dropna().unique()
)

with st.sidebar:
    st.header("Filters")

    course = st.selectbox(
        "Course",
        courses,
    )

# Only show layouts belonging to the selected course
course_df = df_rounds[
    df_rounds["CourseName"] == course
]

layouts = sorted(
    course_df["LayoutName"].dropna().unique()
)

with st.sidebar:
    layout = st.selectbox(
        "Layout",
        layouts,
    )

    # Players belonging to the selected course/layout
    layout_df = course_df[
        course_df["LayoutName"] == layout
    ]

    all_players = sorted(
        layout_df.loc[
            layout_df["PlayerName"] != "Par",
            "PlayerName",
        ].dropna().unique()
    )

    players = st.multiselect(
        "Players",
        all_players,
    )

    after = st.date_input(
        "After",
        value=None,
    )

    before = st.date_input(
        "Before",
        value=None,
    )


# -------------------------------------------------------------------
# Apply filters
# -------------------------------------------------------------------

players_filter = players or ["All"]


df_holes = filter_df(
    df_holes,
    course,
    layout,
    after,
    before,
    players=players_filter,
)

df_rounds = filter_df(
    df_rounds,
    course,
    layout,
    after,
    before,
    players=players_filter,
)


# -------------------------------------------------------------------
# Tabs
# -------------------------------------------------------------------

overview_tab, performance_tab, distribution_tab, holes_tab = st.tabs(
    [
        "Overview",
        "Performance",
        "Score Distribution",
        "Hole Analysis",
    ]
)


# -------------------------------------------------------------------
# Overview
# -------------------------------------------------------------------

with overview_tab:
    st.subheader("Overview")

    stats = get_basic_stats(
        df_holes,
        df_rounds,
    )

    st.text(stats)


# -------------------------------------------------------------------
# Performance
# -------------------------------------------------------------------

with performance_tab:
    st.subheader("Performance Curve")

    col1, col2, col3 = st.columns(3)

    with col1:
        stat = st.selectbox(
            "Statistic",
            ["Total"],
        )

    with col2:
        x_axis_mode = st.radio(
            "X axis",
            ["round", "date"],
            horizontal=True,
        )

    with col3:
        smoothness = st.slider(
            "Smoothness",
            min_value=1,
            max_value=20,
            value=1,
        )

    col1, col2 = st.columns(2)

    with col1:
        hide_par = st.checkbox("Hide par")

    with col2:
        hide_avg = st.checkbox("Hide average")

    plot_data = get_performance_curve(
        csv_dir=csv_dir,
        course=course,
        layout=layout,
        players=players_filter,
        after=after,
        before=before,
        stat=stat,
        hide_par=hide_par,
        x_axis_mode=x_axis_mode,
        hide_avg=hide_avg,
        smoothness=smoothness,
    )

    fig = render_performance_matplotlib(plot_data)

    st.pyplot(fig, width="stretch")


# -------------------------------------------------------------------
# Score distribution
# -------------------------------------------------------------------

with distribution_tab:
    st.subheader("Score Distribution")

    score_counts = get_distribution(
        csv_dir=csv_dir,
        course=course,
        layout=layout,
        players=players_filter,
        after=after,
        before=before,
    )

    fig = render_distribution_matplotlib(score_counts)

    st.pyplot(fig, width="stretch")


# -------------------------------------------------------------------
# Hole analysis
# -------------------------------------------------------------------

with holes_tab:
    st.subheader("Hole Distribution")

    hide_par = st.checkbox(
        "Hide par",
        key="hole_hide_par",
    )

    plot_data = get_hole_distribution(
        csv_dir=csv_dir,
        course=course,
        layout=layout,
        players=players_filter,
        after=after,
        before=before,
    )

    fig = render_hole_distribution_matplotlib(
        plot_data,
        hide_par,
    )

    st.pyplot(fig, width="stretch")
