from pathlib import Path

import pandas as pd


def load_and_format_csv(file):
    df = pd.read_csv(file)

    # Normalize smart quotes in all string columns
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].str.replace("[“”]", '"', regex=True)

    # Normalize timestamps to UTC
    df["StartDate"] = pd.to_datetime(
        df["StartDate"],
        errors="coerce",
        utc=True,
    )

    df["EndDate"] = pd.to_datetime(
        df["EndDate"],
        errors="coerce",
        utc=True,
    )

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

    if after_date is not None:
        after_date = pd.Timestamp(after_date)
        if after_date.tzinfo is None:
            after_date = after_date.tz_localize("UTC")
        else:
            after_date = after_date.tz_convert("UTC")

        df = df[df["StartDate"] >= after_date]

    if before_date is not None:
        before_date = pd.Timestamp(before_date)
        if before_date.tzinfo is None:
            before_date = before_date.tz_localize("UTC")
        else:
            before_date = before_date.tz_convert("UTC")

        df = df[df["StartDate"] <= before_date]

    if players and players[0] != "All":
        df = df[df["PlayerName"].isin(players)]

    if stat:
        # Stats with 0 are not valid because they are not filled in
        df = df[df[stat] != 0]

    return df

