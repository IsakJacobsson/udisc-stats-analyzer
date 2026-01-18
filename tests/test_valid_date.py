import argparse

import pandas as pd
import pytest

from udisc_analysis import valid_date


@pytest.mark.parametrize(
    "date_str",
    [
        "2024-01-15",
        "1999-12-31",
        "2020-02-29",
    ],
)
def test_valid_date_accepts_valid_date_string(date_str):
    result = valid_date(date_str)
    assert isinstance(result, pd.Timestamp)


@pytest.mark.parametrize(
    "invalid_input",
    [
        "",
        "2024-13-01",  # 13 is not a month
        "2024-01-32",  # 32 is not a date in any month
        "foo",  # Not a date
    ],
)
def test_valid_date_rejects_invalid_date_string(invalid_input):
    with pytest.raises(argparse.ArgumentTypeError) as exc_info:
        valid_date("not-a-date")
