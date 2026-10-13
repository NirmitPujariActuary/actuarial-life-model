# Actuarial Life Table and Life Products

A small Python project that reads a mortality table from a CSV file and
calculates survival probabilities, life annuities, life insurances and
net annual premiums.

## Project Overview

The program calculates:

- survival and death probabilities from a mortality table
- curtate life expectancy
- annuity-immediate and annuity-due values (term and whole life)
- term and whole-life insurance values
- level annual net premiums using the equivalence principle

Everything is discrete and annual. Interest is an annual effective rate.

## Actuarial Concepts

- **qx**: probability that a life aged x dies before reaching x+1.
- **px**: probability that a life aged x survives to x+1. px = 1 - qx.
- **Survival probability** (n p x): probability that a life aged x survives
  n years. n p x = px * p(x+1) * ... * p(x+n-1).
- **Discount factor** v = 1 / (1 + i): the value today of 1 paid in one year.
  The related quantity d = i / (1 + i) = 1 - v is the annual discount rate.
- **Life annuity**: payments of 1 per year while the life survives.
  Annuity-immediate (a) pays at the end of each year; annuity-due (a-due)
  pays at the start of each year. a-due = 1 + a for a whole-life annuity.
- **Term insurance**: pays a sum assured at the end of the year of death if
  death occurs within n years.
- **Whole-life insurance**: pays a sum assured at the end of the year of
  death, whenever it occurs.
- **Net premium**: the premium that covers expected benefits only, with no
  expenses or profit.
- **Equivalence principle**: EPV(premiums) = EPV(benefits). The premium is
  P = EPV(benefits) / a-due, because premiums are paid in advance.

Identity checked by the tests: A_x = 1 - d * a-due_x.

## Timing conventions

- Death benefits are paid at the **end of the year of death**.
- Annuity-immediate payments are at the end of each year (k = 1, 2, ...).
- Annuity-due payments and premiums are at the start of each year (k = 0, 1, ...).
- The mortality table must end at an age where qx = 1.

## OOP Design

```text
LifeTable
    holds mortality data and survival calculations

LifeProduct
    common information for products (table, age, interest rate, v, d)

Annuity(LifeProduct)
    annuity calculations

Insurance(LifeProduct)
    shared code for death benefits

TermInsurance(Insurance)
WholeLifeInsurance(Insurance)
```

- A **class** is a blueprint, for example LifeTable.
- An **object** is one real thing built from a class, for example
  `table = LifeTable("data/mortality.csv")`.
- An **attribute** is data stored in an object, for example `self.age`.
- A **method** is a function belonging to a class, for example
  `table.survival_probability(30, 5)`.
- **Inheritance** means a class reuses another class. `Annuity(LifeProduct)`
  automatically gets the table, age, interest rate, v and d.

### Why products receive a LifeTable object

```python
table = LifeTable("data/mortality.csv")
policy = TermInsurance(table, 30, 0.05)
```

The CSV is opened once, when the `LifeTable` is created. The product is handed
that existing object, so it never opens the file itself. This means:

- you can swap the mortality table (for example 5 rows for AM92) without
  changing any product code;
- several products can share one table;
- products can be tested with a tiny table.

## Project Structure

```text
Life_Model/
├── actuarial_life/
│   ├── __init__.py
│   ├── life_table.py     (LifeTable)
│   └── products.py       (LifeProduct, Annuity, Insurance, ...)
├── data/
│   └── mortality.csv
├── tests/
│   └── test_actuarial.py
├── main.py
├── README.md
└── requirements.txt
```

## Mortality file format

```text
age,qx
30,0.10
31,0.20
...
35,1.00
```

## How to run

Install pytest:

```text
python -m pip install -r requirements.txt
```

Run the example:

```text
python main.py
```

Run the tests:

```text
python -m pytest
```

## Input validation

Clear error messages are raised for: missing file, missing columns, empty file,
non-numeric age or qx, duplicate ages, qx outside 0 to 1, ages outside the
table, non-positive or non-integer terms, negative interest rates, and
negative or non-numeric sums assured.