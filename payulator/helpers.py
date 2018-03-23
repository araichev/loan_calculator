import math
from copy import copy

import numpy as np
import pandas as pd

from . import constants as cs


def freq_to_num(freq, allow_cts=False):
    """
    Map frequency name to number of occurrences per year via
    :const:`NUM_BY_FREQ`.
    If not ``allow_cts``, then remove the ``'continuouly'`` option.
    Raise a ``ValueError`` in case of no frequency match.
    """
    d = copy(cs.NUM_BY_FREQ)
    if not allow_cts:
        del d['continuously']

    try:
        return d[freq]
    except KeyError:
        raise ValueError("Invalid frequency '{!s}'. "
          "Frequency must be one of {!s}".format(freq, list(d.keys())))

def to_date_offset(num_per_year):
    """
    Convert the given number of occurrences per year to its
    corresponding period (Pandas DateOffset object),
    e.g. map 4 to ``pd.DateOffset(months=3)``.
    Return ``None`` if num_per_year is not one of
    ``[1, 2, 3, 4, 6, 12, 26, 52, 365]``.
    """
    k = num_per_year
    if k in [1, 2, 3, 4, 6, 12]:
        d = pd.DateOffset(months=12//k)
    elif k == 26:
        d = pd.DateOffset(weeks=2)
    elif k == 52:
        d = pd.DateOffset(weeks=1)
    elif k == 365:
        d = pd.DateOffset(days=1)
    else:
        d = None
    return d

def compute_period_interest_rate(interest_rate, compounding_freq,
  payment_freq):
    """
    Compute the interest rate per payment period given
    an annual interest rate, a compounding frequency, and a payment
    freq.
    See the function :func:`freq_to_num` for acceptable frequencies.
    """
    i = interest_rate
    j = freq_to_num(compounding_freq, allow_cts=True)
    k = freq_to_num(payment_freq)

    if np.isinf(j):
        return math.exp(i/k) - 1
    else:
        return (1 + i/j)**(j/k) - 1

def build_principal_fn(principal, interest_rate, compounding_freq,
  payment_freq, num_payments):
    """
    Compute the remaining loan principal, the loan balance,
    as a function of the number of payments made.
    Return the resulting function.
    """
    P = principal
    I = compute_period_interest_rate(interest_rate, compounding_freq,
      payment_freq)
    n = num_payments

    def p(t):
        if I == 0:
            return P - t*P/n
        else:
            return P*(1 - ((1 + I)**t - 1)/((1 + I)**n - 1))

    return p

def amortize(principal, interest_rate, compounding_freq, payment_freq,
  num_payments):
    """
    Given the loan parameters

    - ``principal``: (float) amount of loan, that is, the principal
    - ``interest_rate``: (float) nominal annual interest rate
      (not as a percentage), e.g. 0.1 for 10%
    - ``compounding_freq``: (string) compounding frequency;
      one of the keys of :const:`NUM_BY_FREQ`, e.g. 'monthly'
    - ``payment_freq``: (string) payments frequency;
      one of the keys of :const:`NUM_BY_FREQ`, e.g. 'monthly'
    - ``num_payments``: (integer) number of payments in the loan
      term

    return the periodic payment amount due to
    amortize the loan into equal payments occurring at the frequency
    ``payment_freq``.
    See the function :func:`freq_to_num` for valid frequncies.

    Notes:

    - https://en.wikipedia.org/wiki/Amortization_calculator
    - https://www.vertex42.com/ExcelArticles/amortization-calculation.html
    """
    P = principal
    I = compute_period_interest_rate(interest_rate, compounding_freq,
      payment_freq)
    n = num_payments
    if I == 0:
        A = P/n
    else:
        A = P*I/(1 - (1 + I)**(-n))

    return A

def compute_amortized_loan(principal, interest_rate,
  compounding_freq, payment_freq, num_payments, fee=0, start_date=None,
  decimals=2):
    """
    Amortize a loan with the given parameters according to the function
    :func:`amortize`, and return a dictionary with the following keys
    and values:

    - ``'periodic_payment'``: periodic payment amount according to
      amortization
    - ``'payment_schedule'``: DataFrame; schedule of loan payments
      broken into principal payments and interest payments
    - ``'interest_total'``: total interest paid on loan
    - ``'interest_and_fee_total'``: interest_total plus loan fee
    - ``'payment_total'``: total of all loan payments, including the
      loan fee
    - ``'interest_and_fee_total/principal``
    - ``'notes'``: NaN for future notes

    If a start date is given (YYYY-MM-DD string), then include payment
    dates in the payment schedule.
    Round all values to the given number of decimal places, but do not
    round if ``decimals is None``.
    """
    A = amortize(principal, interest_rate, compounding_freq, payment_freq,
      num_payments)
    p = build_principal_fn(principal, interest_rate, compounding_freq,
      payment_freq, num_payments)
    n = num_payments
    f = (pd.DataFrame({'payment_sequence': range(1, n + 1)})
        .assign(beginning_balance=lambda x: (x.payment_sequence - 1).map(p))
        .assign(principal_payment=lambda x: x.beginning_balance.diff(-1)
          .fillna(x.beginning_balance.iat[-1]))
        .assign(interest_payment=lambda x: A - x.principal_payment)
        .assign(ending_balance=lambda x: x.beginning_balance
          - x.principal_payment)
        .assign(notes=np.nan)
    )

    date_offset = to_date_offset(freq_to_num(payment_freq))
    if start_date and date_offset:
        # Kludge for pd.date_range not working easily here;
        # see https://github.com/pandas-dev/pandas/issues/2289
        f['payment_date'] = [pd.Timestamp(start_date)
          + j*date_offset for j in range(n)]

        # Put payment date first
        cols = f.columns.tolist()
        cols.remove('payment_date')
        cols.insert(1, 'payment_date')
        f = f[cols].copy()

    # Bundle result into dictionary
    d = {}
    d['periodic_payment'] = A
    d['payment_schedule'] = f
    d['interest_total'] = f['interest_payment'].sum()
    d['interest_and_fee_total'] = d['interest_total'] + fee
    d['payment_total'] = d['interest_and_fee_total'] + principal
    d['interest_and_fee_total/principal'] =\
      d['interest_and_fee_total']/principal

    if decimals is not None:
        for key, val in d.items():
            if isinstance(val, pd.DataFrame):
                d[key] = val.round(decimals)
            else:
                d[key] = round(val, 2)

    return d

def compute_interest_only_loan(principal, interest_rate,
  payment_freq, num_payments, fee=0, start_date=None,
  decimals=2):
    """
    Create a payment schedule etc. for an interest-only loan
    with the given parameters (see the doctstring of :func:`amortize`).
    Return a dictionary with the following keys and values.

    - ``'payment_schedule'``: DataFrame; schedule of loan payments
      broken into principal payments and interest payments
    - ``'interest_total'``: total interest paid on loan
    - ``'interest_and_fee_total'``: interest_total plus loan fee
    - ``'payment_total'``: total of all loan payments, including the
      loan fee
    - ``'interest_and_fee_total/principal``: interest_and_fee_total/principal
    - ``'notes'``: NaN for future notes

    If a start date is given (YYYY-MM-DD string), then include payment
    dates in the payment schedule.
    Round all values to the given number of decimal places, but do not
    round if ``decimals is None``.
    """
    k = freq_to_num(payment_freq)
    A = principal*interest_rate/k
    n = num_payments
    f = (pd.DataFrame({'payment_sequence': range(1, n + 1)})
        .assign(beginning_balance=principal)
        .assign(principal_payment=0)
        .assign(interest_payment=A)
        .assign(ending_balance=principal)
        .assign(notes=np.nan)
    )
    f.principal_payment.iat[-1] = principal
    f.ending_balance.iat[-1] = 0

    date_offset = to_date_offset(k)
    if start_date and date_offset:
        # Kludge for pd.date_range not working easily here;
        # see https://github.com/pandas-dev/pandas/issues/2289
        f['payment_date'] = [pd.Timestamp(start_date)
          + j*date_offset for j in range(n)]

        # Put payment date first
        cols = f.columns.tolist()
        cols.remove('payment_date')
        cols.insert(1, 'payment_date')
        f = f[cols].copy()

    # Bundle result into dictionary
    d = {}
    d['payment_schedule'] = f
    d['interest_total'] = f['interest_payment'].sum()
    d['interest_and_fee_total'] = d['interest_total'] + fee
    d['payment_total'] = d['interest_and_fee_total'] + principal
    d['interest_and_fee_total/principal'] =\
      d['interest_and_fee_total']/principal

    if decimals is not None:
        for key, val in d.items():
            if isinstance(val, pd.DataFrame):
                d[key] = val.round(decimals)
            else:
                d[key] = round(val, 2)

    return d

def aggregate_payment_schedules(payment_schedules, freq=None):
    """
    Given a list of payment schedules in the form output by the
    function :func:`amortize` do the following.
    If all the schedules have a payment date column, then group by
    payment date and resample at the given frequency by summing.
    Otherwise, group by payment sequence and sum.
    Return resulting DataFrame with the columns

    - ``'payment_date'`` if ``'payment_date'`` is present in all
      schedules given or ``'payment_sequence'`` otherwise
    - ``'principal_payment'``
    - ``'interest_payment'``
    - ``'total_payment'``: sum of principal and interest payments

    """
    if not payment_schedules:
        raise ValueError("No payment schedules given to aggregate")

    if all(['payment_date' in f.columns for f in payment_schedules]):
        # Group by payment date
        g = (
            pd.concat(payment_schedules)
            .filter(['payment_date', 'principal_payment', 'interest_payment'])
            .groupby(pd.Grouper(key='payment_date', freq=freq))
            .sum()
            .sort_index()
            .reset_index()
        )
    else:
        # Group by payment sequence
        g = (
            pd.concat(payment_schedules)
            .filter(['payment_sequence', 'principal_payment', 'interest_payment'])
            .groupby('payment_sequence')
            .sum()
            .sort_index()
            .reset_index()
        )

    # Append total payment column
    g['total_payment'] = g['interest_payment'] + g['principal_payment']

    return g