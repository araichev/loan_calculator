"""
Module defining the Loan class.
"""
from collections import OrderedDict
from pathlib import Path
import numbers
import json
from typing import Optional, Dict

import pandas as pd
import voluptuous as vt
from dataclasses import dataclass

from . import constants as cs
from . import helpers as hp


@dataclass
class Loan:
    """
    Represents a loan.
    Parameters are

    - ``code``: code name for the loan; defaults to a
      timestamp-based code
    - ``kind``: kind of loan; 'amortized' or 'interest_only'
    - ``principal``: amount of loan, that is, the principal
    - ``interest_rate``: nominal annual interest rate
      (not as a percentage), e.g. 0.1 for 10%
    - ``payment_freq``: payments frequency;
      one of the keys of :const:`NUM_BY_FREQ`, e.g. 'monthly'
    - ``compounding_freq``: compounding frequency;
      one of the keys of :const:`NUM_BY_FREQ`, e.g. 'monthly'
    - ``num_payments``: number of payments in the loan
      term
    - ``fee``: loan fee
    - ``first_payment_date``: (YYYY-MM-DD date string) date of first loan
      payment

    """

    code: Optional[str] = None
    kind: str = "amortized"
    principal: float = 1
    interest_rate: float = 0
    payment_freq: str = "monthly"
    compounding_freq: Optional[str] = None
    num_payments: int = 1
    fee: float = 0
    first_payment_date: Optional[str] = None

    def __post_init__(self):
        # Set some defaults
        if self.code is None:
            timestamp = pd.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            self.code = f"loan-{timestamp}"
        if self.compounding_freq is None:
            self.compounding_freq = self.payment_freq

    def summarize(self, decimals: int = 2) -> Dict:
        """
        Return the result of :func:`helpers.summarize_amortized_loan`
        is this Loan is amortized or
        :func:`helpers.summarize_interest_only_loan` if this Loan is
        interest-only.
        """
        result = {}
        if self.kind == "amortized":
            result = hp.summarize_amortized_loan(
                self.principal,
                self.interest_rate,
                self.compounding_freq,
                self.payment_freq,
                self.num_payments,
                self.fee,
                self.first_payment_date,
                decimals=decimals,
            )
        elif self.kind == "interest_only":
            result = hp.summarize_interest_only_loan(
                self.principal,
                self.interest_rate,
                self.payment_freq,
                self.num_payments,
                self.fee,
                self.first_payment_date,
                decimals=decimals,
            )

        return result


def check_loan_params(params: Dict) -> Dict:
    """
    Given a dictionary of the form loan_attribute -> value,
    check the keys and values according to the specification
    in the docstring of :func:`build_loan` (allowing extra keys).
    Raise an error if the specification is not met.
    Otherwise return the dictionary unchanged.
    """

    def check_kind(value):
        kinds = ["amortized", "interest_only"]
        if value in kinds:
            return value
        raise vt.Invalid("Kind must be one on {}".format(kinds))

    def check_pos(value):
        if isinstance(value, numbers.Number) and value > 0:
            return value
        raise vt.Invalid("Not a positive number")

    def check_nneg(value):
        if isinstance(value, numbers.Number) and value >= 0:
            return value
        raise vt.Invalid("Not a nonnegative number")

    def check_pos_int(value):
        if isinstance(value, int) and value > 0:
            return value
        raise vt.Invalid("Not a positive integer")

    def check_freq(value):
        if value in cs.NUM_BY_FREQ:
            return value
        raise vt.Invalid("Frequncy must be one of {}".format(cs.NUM_BY_FREQ.keys()))

    def check_date(value, fmt="%Y-%m-%d"):
        err = vt.Invalid("Not a datestring of the form {}".format(fmt))
        try:
            if value is not None and pd.to_datetime(value, format=fmt):
                return value
            raise err
        except TypeError:
            raise err

    schema = vt.Schema(
        {
            "code": str,
            "kind": check_kind,
            "principal": check_pos,
            "interest_rate": check_nneg,
            "payment_freq": check_freq,
            vt.Optional("compounding_freq"): check_freq,
            "num_payments": check_pos_int,
            "first_payment_date": check_date,
            "fee": check_nneg,
        },
        required=True,
        extra=vt.ALLOW_EXTRA,
    )

    params = schema(params)

    return params


def prune_loan_params(params: Dict) -> Dict:
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


def build_loan(path: Path) -> "Loan":
    """
    Given the path to a JSON file encoding the parameters
    of a loan, read the file, check the parameters,
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
