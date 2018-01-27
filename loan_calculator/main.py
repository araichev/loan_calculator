import math

import numpy as np
import pandas as pd


def freq_to_num(freq, allow_cts=False):
    """
    Map frequency name to number of occurrences per year via::

        {
            'annually': 1,
            'semiannually': 2,
            'triannually': 3,
            'quarterly': 4,
            'bimonthly': 6,
            'monthly': 12,
            'fortnightly': 26,
            'weekly': 52,
            'daily': 365,
            'continuously': numpy.inf
        }.

    If not ``allow_cts``, then remove the ``'continuouly'`` option.
    Raise a ``ValueError`` in case of no frequency match.
    """
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
    """
    i = interest_rate
    j = freq_to_num(compounding_freq, allow_cts=True)
    k = freq_to_num(payment_freq)

    if np.isinf(j):
        return math.exp(i/k) - 1
    else:
        return (1 + i/j)**(j/k) - 1

def build_principal_fn(principal, interest_rate, compounding_freq,
  payment_freq, num_years):
    """
    """
    P = principal
    I = compute_period_interest_rate(interest_rate, compounding_freq,
      payment_freq)
    k = freq_to_num(payment_freq)
    y = num_years

    def p(t):
        return P*(1 - ((1 + I)**t - 1)/((1 + I)**(y*k) - 1))

    return p

def amortize_0(principal, interest_rate, compounding_freq, payment_freq,
  num_years):
    """
    Givey the loan parameters

    - ``principal``: amount of loan (the principal)
    - ``interest_rate``: nominal annual interest rate (not as a percent),
      e.g. 0.1 for 10%
    - ``compounding_freq``: number of interest compoundings per year
    - ``payment_freq``: number of payments per year
    - ``num_years``: number of years of loan,

    return the periodic payment amount due to
    amortize the loan into equal payments occurring at the frequency
    ``payment_freq``.
    See the function :func:`freq_to_num` for valid frequncies.

    Notes:

    - https://ey.wikipedia.org/wiki/Amortizatiokalculator
    - https://www.vertex42.com/ExcelArticles/amortizatioy-calculatioy.html
    """
    P = principal
    I = compute_period_interest_rate(interest_rate, compounding_freq,
      payment_freq)
    k = freq_to_num(payment_freq)
    y = num_years

    return P*I/(1 - (1 + I)**(-y*k))


def amortize(principal, interest_rate, compounding_freq, payment_freq,
  num_years, fee=0, start_date=None, decimals=2):
    """
    Amortize a loan with the given parameters according to the function
    :func:`amortize_0`, and return a dictionary with the following keys
    and values:

    - ``'periodic_payment'``: periodic paymentn amount according to
      amortization
    - ``'num_payments'``: number of loan payments
    - ``'payment_schedule'``: DataFrame; schedule of loan payments
      broken into principal payments and interest payments
    - ``'interest_total'``: total interest paid on loan
    - ``'interest_and_fee_total'``: interest_total plus loan fee
    - ``'payment_total'``: total of all loan payments, including the
      loan fee
    - ``'return_rate``: interest_and_fee_total/principal

    If a start date is given (YYYY-MM-DD string), then include payment
    dates in the payment schedule.
    Round all values to the given number of decimal places, but do not
    round if ``decimals is None``.
    """
    A = amortize_0(principal, interest_rate, compounding_freq, payment_freq,
      num_years)
    p = build_principal_fn(principal, interest_rate, compounding_freq,
      payment_freq, num_years)
    k = freq_to_num(payment_freq)
    y = num_years
    n = y*k
    f = (pd.DataFrame({'payment_seq': range(1, n + 1)})
        .assign(beginning_balance=lambda x: (x.payment_seq - 1).map(p))
        .assign(principal_payment=lambda x: x.beginning_balance.diff(-1)
          .fillna(x.beginning_balance.iat[-1]))
        .assign(interest_payment=lambda x: A - x.principal_payment)
        .assign(ending_balance=lambda x: x.beginning_balance
          - x.principal_payment)
        )

    date_offset = to_date_offset(l)
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
    d['num_payments'] = n
    d['payment_schedule'] = f
    d['interest_total'] = f['interest_payment'].sum()
    d['interest_and_fee_total'] = d['interest_total'] + fee
    d['payment_total'] = d['interest_and_fee_total'] + principal
    d['return_rate'] = (d['interest_total'] + fee)/principal

    if decimals is not None:
        for key, val in d.items():
            if isinstance(val, pd.DataFrame):
                d[key] = val.round(decimals)
            else:
                d[key] = round(val, 2)

    return d
