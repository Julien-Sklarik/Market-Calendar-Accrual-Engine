import pandas as pd
from market_calendar import accrual_date, payment_date

def main():
    stl = pd.Timestamp("20240131")
    next_acc = accrual_date(stl, n_periods=1, freq="M")
    pay = payment_date(next_acc)

    print("Settlement", stl.date())
    print("Next accrual", next_acc.date())
    print("Payment date", pay.date())

if __name__ == "__main__":
    main()
