import pytest

from .context import payulator, ROOT
from payulator import *


def test_summarize():
    for kind in ["amortized", "interest_only"]:
        loan = Loan(kind=kind)
        get = loan.summarize()

        if kind == "amortized":
            expect = summarize_amortized_loan(
                loan.principal,
                loan.interest_rate,
                loan.compounding_freq,
                loan.payment_freq,
                loan.num_payments,
            )
        elif kind == "interest_only":
            expect = summarize_interest_only_loan(
                loan.principal, loan.interest_rate, loan.payment_freq, loan.num_payments
            )

        for k, v in expect.items():
            if isinstance(v, pd.DataFrame):
                assert pd.DataFrame.equals(get[k], v)
            else:
                assert get[k] == v


def test_check_loan_params():
    params = {
        "code": "test-20180324",
        "principal": 10000,
        "interest_rate": 0.12,
        "kind": "amortized",
        "num_payments": 6,
        "payment_freq": "monthly",
        "first_payment_date": "2018-03-24",
        "fee": 250,
        "bingo": "bongo",
    }
    assert params == check_loan_params(params)

    p = copy(params)
    p["fee"] = "whoops"
    with pytest.raises(vt.MultipleInvalid):
        check_loan_params(p)

    p = copy(params)
    p["interest_rate"] = -1
    with pytest.raises(vt.MultipleInvalid):
        check_loan_params(p)

    p = copy(params)
    p["first_payment_date"] = "23-02-2018"
    with pytest.raises(vt.MultipleInvalid):
        check_loan_params(p)


def test_build_loan():
    DATA_DIR = ROOT / "tests" / "data"

    path = DATA_DIR / "good_loan_params.json"
    loan = build_loan(path)
    assert isinstance(loan, Loan)

    path = DATA_DIR / "bad_loan_params.json"
    with pytest.raises(vt.MultipleInvalid):
        build_loan(path)
