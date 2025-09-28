import pandas as pd

from market_calendar import (
    holidays_span,
    is_business_day,
    is_last_day_of_month,
    modified_following,
    accrual_date,
    add_business_days,
    payment_date,
    accrual_period_days,
)

def test_is_business_day_weekend_and_weekday():
    hol = holidays_span(2024, 2024)
    saturday = pd.Timestamp("20240106")
    monday = pd.Timestamp("20240108")
    assert is_business_day(saturday, hol) is False
    assert is_business_day(monday, hol) is True

def test_modified_following_month_change_rolls_back():
    d = pd.Timestamp("20240831")  # Saturday, next business day would be Sep which triggers rollback
    hol = holidays_span(2024, 2024)
    adj = modified_following(d, hol)
    assert adj == pd.Timestamp("20240830")

def test_is_last_day_of_month_true_and_false():
    assert is_last_day_of_month(pd.Timestamp("20240229")) is True
    assert is_last_day_of_month(pd.Timestamp("20240228")) is False

def test_accrual_date_last_day_rule_monthly():
    stl = pd.Timestamp("20240131")
    acc = accrual_date(stl, n_periods=1, freq="M")
    assert acc == pd.Timestamp("20240229")

def test_accrual_date_quarterly_weekend_adjust():
    stl = pd.Timestamp("20240315")
    acc = accrual_date(stl, n_periods=1, freq="Q")
    assert acc == pd.Timestamp("20240617")

def test_payment_date_t_plus_two_business_days():
    accr = pd.Timestamp("20240702")
    pay = payment_date(accr)
    assert pay == pd.Timestamp("20240705")

def test_add_business_days_across_us_holiday():
    start = pd.Timestamp("20240112")  # Friday
    hol = holidays_span(2024, 2024)
    # Monday 20240115 is MLK Day in US, included in the union set
    out = add_business_days(start, 3, hol)
    assert out == pd.Timestamp("20240118")

def test_accrual_period_days_simple_window():
    days = accrual_period_days("20240101", "20240131")
    assert days == 30
