from itertools import product

import pandas as pd
import pytest

from .context import payulator
from payulator import *


def test_freq_to_num():
    d = {
        'annually': 1,
        'semiannually': 2,
        'triannually': 3,
        'quarterly': 4,
        'bimonthly': 6,
        'monthly': 12,
        'fortnightly': 26,
        'weekly': 52,
        'daily': 365,
        'continuously': np.inf,
    }
    for allow_cts in [True, False]:
        # Test on valid freq names
        for key, val in d.items():
            if key == 'continuously' and not allow_cts:
                with pytest.raises(ValueError):
                    freq_to_num(key, allow_cts=allow_cts)
            else:
                assert freq_to_num(key, allow_cts=allow_cts) == val

        # Test on invalid freq name
        with pytest.raises(ValueError):
            freq_to_num('bingo', allow_cts=allow_cts)

def test_to_date_offset():
    for k in [1, 2, 3, 4, 6, 12, 26, 52, 365]:
        assert isinstance(to_date_offset(k), pd.DateOffset)

    assert to_date_offset(10) is None

def test_amortize_0():
    # Compare a few outputs to those of
    # https://www.calculator.net/business-loan-calculator.html
    A = amortize_0(1000, 0.05, 'quarterly', 'monthly', 3*12)
    assert round(A, 2) == 29.96

    A = amortize_0(1000, 0.02, 'continuously', 'semiannually', 2*2)
    assert round(A, 2) == 256.31

def test_compute_period_interest_rate():
    I = compute_period_interest_rate(0.12, 'monthly', 'monthly')
    assert round(I, 2) == 0.01

def test_build_principal_fn():
    balances = [
        100.00,
        91.93,
        83.81,
        75.65,
        67.44,
        59.18,
        50.87,
        42.52,
        34.11,
        25.66,
        17.16,
        8.60,
        0,
    ]
    p = build_principal_fn(100, 0.07, 'monthly', 'monthly', 12)
    for i in range(13):
        assert round(p(i), 2) == balances[i]

def test_compute_amortized_loan():
    # Compare a few outputs to those of
    # https://www.calculator.net/business-loan-calculator.html
    A = compute_amortized_loan(1000, 0.05, 'quarterly', 'monthly',
      3*12, fee=10)
    expect_keys = {
        'periodic_payment',
        'payment_schedule',
        'interest_total',
        'interest_and_fee_total',
        'payment_total',
        'interest_and_fee_total/principal',
    }
    assert set(A.keys()) == expect_keys
    assert round(A['periodic_payment'], 2) == 29.96
    assert round(A['interest_and_fee_total'], 2) == 88.62
    assert A['payment_schedule'].shape[0] == 3*12

def test_aggregate_payment_schedules():
    # Compare a few outputs to those of
    # https://www.calculator.net/business-loan-calculator.html
    for start_date, agg_key in [(None, 'payment_sequence'),
      ('2018-01-01', 'payment_date')]:
        A = compute_amortized_loan(1000, 0.05, 'quarterly', 'monthly', 3*12, fee=10,
          start_date=start_date)
        B = compute_amortized_loan(1000, 0.05, 'quarterly', 'monthly', 3*12, fee=10,
          start_date=start_date)
        f = aggregate_payment_schedules([A['payment_schedule'],
          B['payment_schedule']])
        expect_cols = {
            agg_key,
            'interest_payment',
            'principal_payment',
            'total_payment',
        }
        assert set(f.columns) == expect_cols
