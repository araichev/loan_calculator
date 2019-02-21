Payulator
*********
.. image:: http://mybinder.org/badge.svg
    :target: http://mybinder.org:/repo/araichev/payulator

.. image:: https://travis-ci.org/araichev/payulator.svg?branch=master
    :target: https://travis-ci.org/araichev/payulator

A small Python 3.6+ library that calculates loan payments.
Similar to the business loan calculator at `Calculator.net <https://www.calculator.net/business-loan-calculator.html>`_.


Installation
============
Using Poetry, do ``poetry install --git https://github.com/araichev/payulator yayulator``


Usage
=====
Play with the examples in the Jupyter notebook at ``ipynb/examples.ipynb``
You can even do so online by clicking the Binder badge above.


Authors
=======
- Alex Raichev, 2018-01-20


Documentation
=============
On Github Pages `here <https://raichev.net/payulator_docs/>`_.


Changes
=======

3.0.1, 2019-02-22
-----------------
- Switched to Poetry
- Switched to Python 3.6
- Used data class


3.0.0, 2018-03-24
-----------------
- Changed function names
- Added a Loan class


2.0.0, 2018-03-10
-----------------
- Changed function names
- Replaced number of years with number of payments
- Added a function to compute interest-only loans


1.1.0, 2018-03-03
-----------------
- Added the function ``aggregate_payment_schedules``


1.0.0, 2018-01-27
------------------
- First release
