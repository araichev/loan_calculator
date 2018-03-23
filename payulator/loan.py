from collections import OrderedDict
from pathlib import Path

import pandas as pd
import voluptuous as vt

from . import constants as cs
from . import helpers as hp


class Loan(object):
    """
    An instance of this class is a representation of a loan with
    the parameters listed in :func:`__init__`.
    """

    def __init__(self, code=None,
      kind='amortized', principal=1, interest_rate=0,
      payment_freq='monthly', compounding_freq=None,
      num_payments=1, fee=0, start_date=None):
        """
        Parameters are

        - ``code``: (string) code name for the loan; defaults to a
          timestamp-based code
        - ``kind``: (string) kind of loan;
          'amortized' or 'interest_only'
        - ``principal``: (float) amount of loan, that is, the principal
        - ``interest_rate``: (float) nominal annual interest rate
          (not as a percentage), e.g. 0.1 for 10%
        - ``payment_freq``: (string) payments frequency;
          one of the keys of :const:`NUM_BY_FREQ`, e.g. 'monthly'
        - ``compounding_freq``: (string) compounding frequency;
          one of the keys of :const:`NUM_BY_FREQ`, e.g. 'monthly'
        - ``num_payments``: (integer) number of payments in the loan
          term
        """
        timestamp = pd.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        self.code = code or 'loan-' + timestamp
        self.kind = kind
        self.principal = principal
        self.interest_rate = interest_rate
        self.payment_freq = payment_freq
        self.compounding_freq = compounding_freq or payment_freq
        self.num_payments = num_payments
        self.start_date = start_date
        self.fee = fee

    def to_dict(self, ordered=False):
        if ordered:
            d = OrderedDict()
        else:
            d = dict()

        for k in cs.LOAN_ATTRS:
            d[k] = getattr(self, k)

        return d

    def __str__(self):
        d = self.to_dict(ordered=True)
        s = ['{}: {}'.format(k, v) for k, v in d.items()]
        return '\n'.join(s)

    def summarize(self, decimals=2):
        """
        Return the result of :func:`helpers.compute_amortized_loan`
        for an amortized loan or
        :func:`helpers.compute_interest_only_loan` for an interest-only
        loan.
        """
        result = {}
        if self.kind == 'amortized':
            result = hp.compute_amortized_loan(self.principal,
              self.interest_rate, self.compounding_freq,
              self.payment_freq, self.num_payments,
              self.fee, self.start_date, decimals=decimals)
        elif self.kind == 'interest_only':
            result = hp.compute_interest_only_loan(self.principal,
              self.interest_rate,
              self.payment_freq, self.num_payments,
              self.fee, self.start_date, decimals=decimals)

        return result


def check_loan_params(params):
    """
    Given a dictionary of the form loan_attribute -> value,
    check the keys and values according to the specification
    in the docstring of :func:`read_loan` (allowing extra keys).
    Raise an error if the specification is not met.
    Otherwise return the dictionary unchanged.
    """
    def check_kind(value):
        kinds = ['amortized', 'interest_only']
        if value in kinds:
            return value
        raise vt.Invalid('Kind must be one on {}'.format(
          kinds))

    def check_pos(value):
        if value > 0:
            return value
        raise vt.Invalid("Not a positive number")

    check_nneg = vt.Schema(vt.Range(min=0))

    def check_pos_int(value):
        if isinstance(value, int) and value > 0:
            return value
        raise vt.Invalid("Not a positive integer")

    def check_freq(value):
        if value in cs.NUM_BY_FREQ:
            return value
        raise vt.Invalid("Frequncy must be one of {}".format(
          cs.NUM_BY_FREQ.keys()))

    def check_date(value, fmt='%Y-%m-%d'):
        err = vt.Invalid('Not a datestring of the form {}'.format(fmt))
        try:
            if value is not None and pd.to_datetime(value, format=fmt):
                return value
            raise err
        except TypeError:
            raise err

    schema = vt.Schema({
        'code': str,
        'kind': check_kind,
        'principal': check_pos,
        'interest_rate': check_nneg,
        'payment_freq': check_freq,
        vt.Optional('compounding_freq'): check_freq,
        'num_payments': check_pos_int,
        'start_date': check_date,
        'fee': check_nneg,
    }, required=True, extra=vt.ALLOW_EXTRA)

    params = schema(params)

    return params

def prune_loan_params(params):
    """
    Given a dictionary of loan parameters, remove the keys
    not in :const:`LOAN_ATTRS` and return the resulting,
    possibly empty dictionary.
    """
    new_params = {}
    for key in params:
        if key in cs.LOAN_ATTRS:
            new_params[key] = params[key]

    return new_params

def read_loan(path):
    """
    Given the path to a JSON file encoding the parameters
    of a loan, read the file, check the paramaters,
    and return a Loan instance with those parameters.

    The keys and values of the JSON dictionary should contain

    - ``code``: (string) code name for the loan
    - ``kind``: (string) kind of loan; 'amortized' or 'interest_only'
    - ``principal``: (float) amount of loan, that is, the principal
    - ``interest_rate``: (float) nominal annual interest rate
      (not as a percentage), e.g. 0.1 for 10%
    - ``payment_freq``: (string) payments frequency;
      one of the keys of :const:`NUM_BY_FREQ`, e.g. 'monthly'
    - ``compounding_freq``: (string) compounding frequency;
      one of the keys of :const:`NUM_BY_FREQ`, e.g. 'monthly'
    - ``num_payments``: (integer) number of payments in the loan
      term

    Extra keys and values are allowed but will be ignored in
    the returned Loan instance.
    """
    # Read file
    with Path(path).open() as src:
        params = json.load(src)

    # Check params
    params = check_loan_params(params)

    # Remove extra params
    params = prune_loan_params(params)

    return Loan(**params)
