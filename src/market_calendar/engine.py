import pandas as pd
import holidays
from functools import lru_cache

# ------------------------------------------------------------------
# 1. Holidays helpers
# ------------------------------------------------------------------
@lru_cache  # évite de recalculer pour la même année
def _holidays_year(year: int) -> set[pd.Timestamp]:
    """US + UK holidays for a given year, as pd.Timestamp."""
    raw = set(holidays.US(years=year).keys()) | set(holidays.UK(years=year).keys())
    return {pd.Timestamp(d) for d in raw}

def holidays_span(start_year: int, end_year: int) -> set[pd.Timestamp]:
    out = set()
    for y in range(start_year, end_year + 1):
        out |= _holidays_year(y)
    return out

def is_business_day(date: pd.Timestamp, hol_set: set[pd.Timestamp]) -> bool:
    return date.weekday() < 5 and date.normalize() not in hol_set  # normalise à 00:00

# ------------------------------------------------------------------
# 2. Calendar conventions
# ------------------------------------------------------------------
def is_last_day_of_month(dt: pd.Timestamp) -> bool:
    return dt == (dt + pd.offsets.MonthEnd(0))

def modified_following(date: pd.Timestamp,
                       hol_set: set[pd.Timestamp]) -> pd.Timestamp:
    """'Modified-Following' selon les slides : avance, puis rollback si mois change."""
    d = date
    # roll forward jusqu'à business day
    while not is_business_day(d, hol_set):
        d += pd.Timedelta(days=1)
        if d.year not in {h.year for h in hol_set}:
            hol_set |= _holidays_year(d.year)

    # si on a changé de mois, on revient au business day précédent
    if d.month != date.month:
        d -= pd.Timedelta(days=1)
        while not is_business_day(d, hol_set):
            d -= pd.Timedelta(days=1)
    return d

# ------------------------------------------------------------------
# 3. Accrual / payment dates
# ------------------------------------------------------------------
def accrual_date(settlement: str | pd.Timestamp,
                 n_periods: int = 1,
                 freq: str = 'Y') -> pd.Timestamp:
    stl = pd.Timestamp(settlement)

    # 1. Raw unadjusted date
    if freq == 'Y':
        unadj = stl + pd.DateOffset(years=n_periods)
    elif freq == 'Q':
        unadj = stl + pd.DateOffset(months=3 * n_periods)
    elif freq == 'M':
        unadj = stl + pd.DateOffset(months=n_periods)
    elif freq == 'W':
        unadj = stl + pd.DateOffset(weeks=n_periods)
    else:
        raise ValueError("freq must be Y, Q, M or W")

    # 2. Align day-of-month (except if last-day-of-month rule)
    if is_last_day_of_month(stl) and freq in {'Y', 'Q', 'M'}:
        unadj = unadj + pd.offsets.MonthEnd(0)
    elif freq in {'Y', 'Q', 'M'}:
        # conserve le 'jour' d'origine si possible
        try:
            unadj = unadj.replace(day=stl.day)
        except ValueError:
            # ex : passer du 31-jan au 31-feb → recule jusqu'à date valide
            unadj = unadj + pd.offsets.MonthEnd(0)

    # 3. Business-day adjustment
    hol_set = holidays_span(stl.year - 1, unadj.year + 1)  # marge de sécurité
    return modified_following(unadj, hol_set)

def add_business_days(start: pd.Timestamp,
                      n: int,
                      hol_set: set[pd.Timestamp]) -> pd.Timestamp:
    d = start
    added = 0
    while added < n:
        d += pd.Timedelta(days=1)
        if is_business_day(d, hol_set):
            added += 1
    return d

def payment_date(accrual: str | pd.Timestamp) -> pd.Timestamp:
    accr = pd.Timestamp(accrual)
    hol_set = holidays_span(accr.year, accr.year + 1)
    return add_business_days(accr, 2, hol_set)

# ------------------------------------------------------------------
# 4. Day-count
# ------------------------------------------------------------------
def accrual_period_days(start: str | pd.Timestamp,
                        end: str | pd.Timestamp) -> int:
    """ACT/360 convention – start exclusive, end inclusive."""
    return (pd.Timestamp(end) - pd.Timestamp(start)).days