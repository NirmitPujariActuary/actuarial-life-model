import pytest
from actuarial_life.life_table import LifeTable
from actuarial_life.products import LifeProduct, Annuity, Insurance, TermInsurance, WholeLifeInsurance


# ---------- helper and fixture ----------

def write_csv(tmp_path, text):
    """Write text into a temporary CSV file and return its filename."""
    file_path = tmp_path / "test_table.csv"
    file_path.write_text(text)
    return str(file_path)

@pytest.fixture
def table(tmp_path):
    """A small 6-row mortality table, rebuilt fresh for each test."""
    filename = write_csv(tmp_path, "age,qx\n30,0.10\n31,0.20\n32,0.30\n33,0.40\n34,0.50\n35,1.00\n")
    return LifeTable(filename)


# ---------- LifeTable calculation tests ----------

def test_qx(table):
    assert table.qx(30) == 0.10
    assert table.qx(33) == 0.40


def test_px(table):
    assert table.px(30) == pytest.approx(0.90)
    assert table.px(34) == pytest.approx(0.50)


def test_survival_probability(table):
    # 5p30 = 0.9 * 0.8 * 0.7 * 0.6 * 0.5
    assert table.survival_probability(30, 5) == pytest.approx(0.1512)
    # 2p31 = 0.8 * 0.7
    assert table.survival_probability(31, 2) == pytest.approx(0.56)


def test_survival_probability_zero_years(table):
    assert table.survival_probability(30, 0) == 1.0


def test_death_probability(table):
    assert table.death_probability(30, 5) == pytest.approx(1 - 0.1512)


def test_life_expectancy(table):
    # 0.9 + 0.72 + 0.504 + 0.3024 + 0.1512
    assert table.life_expectancy(30) == pytest.approx(2.5776)


# ---------- CSV error tests ----------

def test_file_does_not_exist():
    with pytest.raises(FileNotFoundError, match="was not found"):
        LifeTable("data/no_such_file.csv")


def test_missing_age_column(tmp_path):
    filename = write_csv(tmp_path, "years,qx\n30,0.10\n")
    with pytest.raises(ValueError, match="'age' column"):
        LifeTable(filename)


def test_missing_qx_column(tmp_path):
    filename = write_csv(tmp_path, "age,rate\n30,0.10\n")
    with pytest.raises(ValueError, match="'qx' column"):
        LifeTable(filename)


def test_qx_not_numeric(tmp_path):
    filename = write_csv(tmp_path, "age,qx\n30,abc\n")
    with pytest.raises(ValueError, match="qx must be a number"):
        LifeTable(filename)


def test_age_not_numeric(tmp_path):
    filename = write_csv(tmp_path, "age,qx\nthirty,0.10\n")
    with pytest.raises(ValueError, match="Age must be a whole number"):
        LifeTable(filename)


def test_duplicate_ages(tmp_path):
    filename = write_csv(tmp_path, "age,qx\n30,0.10\n30,0.20\n")
    with pytest.raises(ValueError, match="more than once"):
        LifeTable(filename)


def test_empty_csv(tmp_path):
    filename = write_csv(tmp_path, "")
    with pytest.raises(ValueError, match="empty"):
        LifeTable(filename)


def test_header_only_csv(tmp_path):
    filename = write_csv(tmp_path, "age,qx\n")
    with pytest.raises(ValueError, match="no data rows"):
        LifeTable(filename)


# ---------- mortality and age error tests ----------

def test_negative_qx(tmp_path):
    filename = write_csv(tmp_path, "age,qx\n45,-0.1\n")
    with pytest.raises(ValueError, match="qx must be between 0 and 1 for age 45"):
        LifeTable(filename)


def test_qx_above_one(tmp_path):
    filename = write_csv(tmp_path, "age,qx\n45,1.5\n")
    with pytest.raises(ValueError, match="qx must be between 0 and 1 for age 45"):
        LifeTable(filename)


def test_age_outside_table(table):
    with pytest.raises(ValueError, match="Age 20 is outside the available mortality table"):
        table.qx(20)


def test_age_not_a_number_in_method(table):
    with pytest.raises(ValueError, match="Age must be a whole number"):
        table.qx("thirty")


def test_negative_years(table):
    with pytest.raises(ValueError, match="Years cannot be negative"):
        table.survival_probability(30, -1)

# ---------- Annuity tests ----------

def test_term_annuity(table):
    # a_{30:2} = 0.9/1.05 + 0.72/1.05^2
    annuity = Annuity(table, 30, 0.05)
    expected = 0.9 / 1.05 + 0.72 / 1.05 ** 2
    assert annuity.term_annuity(2) == pytest.approx(expected)


def test_term_annuity_due(table):
    # a-due_{30:2} = 1 + 0.9/1.05
    annuity = Annuity(table, 30, 0.05)
    expected = 1 + 0.9 / 1.05
    assert annuity.term_annuity_due(2) == pytest.approx(expected)


def test_whole_life_annuity(table):
    # a_30 = sum of v^k * kp30 for k = 1 to 5 (6p30 = 0)
    annuity = Annuity(table, 30, 0.05)
    expected = (0.9 / 1.05 + 0.72 / 1.05 ** 2 + 0.504 / 1.05 ** 3
                + 0.3024 / 1.05 ** 4 + 0.1512 / 1.05 ** 5)
    assert annuity.whole_life_annuity() == pytest.approx(expected)


def test_whole_life_annuity_due(table):
    # a-due_30 = 1 + a_30 (the table ends with qx = 1)
    annuity = Annuity(table, 30, 0.05)
    assert annuity.whole_life_annuity_due() == pytest.approx(1 + annuity.whole_life_annuity())


# ---------- Insurance tests ----------

def test_term_insurance(table):
    # k=0: v * q30     k=1: v^2 * p30 * q31
    policy = TermInsurance(table, 30, 0.05)
    expected = 1000000 * (0.1 / 1.05 + 0.9 * 0.2 / 1.05 ** 2)
    assert policy.term_insurance(2, 1000000) == pytest.approx(expected)


def test_whole_life_insurance(table):
    # sum of v^(k+1) * kp30 * q(30+k) for k = 0 to 5
    policy = WholeLifeInsurance(table, 30, 0.05)
    expected = (0.1 / 1.05
                + 0.9 * 0.2 / 1.05 ** 2
                + 0.72 * 0.3 / 1.05 ** 3
                + 0.504 * 0.4 / 1.05 ** 4
                + 0.3024 * 0.5 / 1.05 ** 5
                + 0.1512 * 1.0 / 1.05 ** 6)
    assert policy.whole_life_insurance(1) == pytest.approx(expected)


# ---------- Premium tests ----------

def test_net_annual_premium(table):
    # P = EPV(benefits) / a-due_{30:2}
    policy = TermInsurance(table, 30, 0.05)
    benefits = 1000000 * (0.1 / 1.05 + 0.9 * 0.2 / 1.05 ** 2)
    annuity_due = 1 + 0.9 / 1.05
    assert policy.net_annual_premium(2, 1000000) == pytest.approx(benefits / annuity_due)


def test_premium_equivalence(table):
    # Premium * annuity-due must give back the EPV of benefits
    policy = TermInsurance(table, 30, 0.05)
    annuity = Annuity(table, 30, 0.05)
    premium = policy.net_annual_premium(2, 1000000)
    assert premium * annuity.term_annuity_due(2) == pytest.approx(policy.term_insurance(2, 1000000))


# ---------- Mathematical identity: A_x = 1 - d * a-due_x ----------

def test_whole_life_identity(table):
    interest = 0.05
    d = interest / (1 + interest)

    left_side = WholeLifeInsurance(table, 30, interest).whole_life_insurance(1)
    right_side = 1 - d * Annuity(table, 30, interest).whole_life_annuity_due()

    assert left_side == pytest.approx(right_side)


# ---------- Product error tests ----------

def test_negative_interest(table):
    with pytest.raises(ValueError, match="Interest rate cannot be negative"):
        LifeProduct(table, 30, -0.01)


def test_interest_not_numeric(table):
    with pytest.raises(ValueError, match="Interest rate must be a number"):
        LifeProduct(table, 30, "five percent")


def test_product_age_outside_table(table):
    with pytest.raises(ValueError, match="Age 20 is outside the available mortality table"):
        LifeProduct(table, 20, 0.05)


def test_product_age_not_numeric(table):
    with pytest.raises(ValueError, match="Age must be a whole number"):
        LifeProduct(table, "thirty", 0.05)


def test_product_needs_a_life_table():
    with pytest.raises(ValueError, match="must be a LifeTable object"):
        LifeProduct("data/mortality.csv", 30, 0.05)


def test_term_zero(table):
    policy = TermInsurance(table, 30, 0.05)
    with pytest.raises(ValueError, match="Term must be greater than 0"):
        policy.term_insurance(0, 1000)


def test_term_negative(table):
    annuity = Annuity(table, 30, 0.05)
    with pytest.raises(ValueError, match="Term must be greater than 0"):
        annuity.term_annuity(-3)


def test_term_not_whole_number(table):
    annuity = Annuity(table, 30, 0.05)
    with pytest.raises(ValueError, match="Term must be a whole number"):
        annuity.term_annuity(2.5)


def test_negative_sum_assured(table):
    policy = TermInsurance(table, 30, 0.05)
    with pytest.raises(ValueError, match="Sum assured cannot be negative"):
        policy.term_insurance(2, -5)


def test_sum_assured_not_numeric(table):
    policy = WholeLifeInsurance(table, 30, 0.05)
    with pytest.raises(ValueError, match="Sum assured must be a number"):
        policy.whole_life_insurance("a lot")


def test_term_runs_past_end_of_table(table):
    policy = TermInsurance(table, 30, 0.05)
    with pytest.raises(ValueError, match="outside the available mortality table"):
        policy.term_insurance(10, 1000)


def test_premium_term_zero(table):
    policy = TermInsurance(table, 30, 0.05)
    with pytest.raises(ValueError, match="Term must be greater than 0"):
        policy.net_annual_premium(0, 1000)