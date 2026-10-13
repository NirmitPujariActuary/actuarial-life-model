from actuarial_life.life_table import LifeTable


class LifeProduct:
    """Common information needed by every life product.

    A product is given a LifeTable object (it does NOT read the CSV itself),
    plus the age of the policyholder and an annual effective interest rate.
    """

    def __init__(self, life_table, age, interest_rate):
        # --- check the inputs ---
        if not isinstance(life_table, LifeTable):
            raise ValueError("life_table must be a LifeTable object.")

        life_table.check_age(age)    # raises a clear error if age is bad or outside the table

        if not isinstance(interest_rate, (int, float)):
            raise ValueError("Interest rate must be a number.")
        if interest_rate < 0:
            raise ValueError("Interest rate cannot be negative.")

        # --- store the inputs as attributes ---
        self.life_table = life_table
        self.age = age
        self.interest_rate = interest_rate

        # --- discount quantities, calculated once ---
        self.v = 1 / (1 + interest_rate)                # discount factor
        self.d = interest_rate / (1 + interest_rate)    # annual discount rate

    def check_term(self, term):
        """Make sure the term is a positive whole number of years."""
        if not isinstance(term, int):
            raise ValueError("Term must be a whole number of years.")
        if term <= 0:
            raise ValueError("Term must be greater than 0.")


class Annuity(LifeProduct):
    """Annuity values. Payments are of 1 per year, paid while the life survives."""

    # ---------- annuity-immediate: paid at the END of each year ----------

    def term_annuity(self, term):
        """a_{x:n} = sum of v^k * kp_x for k = 1 to n."""
        self.check_term(term)
        total = 0.0
        for k in range(1, term + 1):
            survival = self.life_table.survival_probability(self.age, k)
            total = total + (self.v ** k) * survival
        return total

    def whole_life_annuity(self):
        """a_x = sum of v^k * kp_x for k = 1 until the end of the table."""
        years_left = self.life_table.max_age - self.age + 1
        total = 0.0
        for k in range(1, years_left + 1):
            survival = self.life_table.survival_probability(self.age, k)
            total = total + (self.v ** k) * survival
        return total

    # ---------- annuity-due: paid at the START of each year ----------

    def term_annuity_due(self, term):
        """a-due_{x:n} = sum of v^k * kp_x for k = 0 to n-1."""
        self.check_term(term)
        total = 0.0
        for k in range(0, term):
            survival = self.life_table.survival_probability(self.age, k)
            total = total + (self.v ** k) * survival
        return total

    def whole_life_annuity_due(self):
        """a-due_x = sum of v^k * kp_x for k = 0 until the end of the table."""
        years_left = self.life_table.max_age - self.age
        total = 0.0
        for k in range(0, years_left + 1):
            survival = self.life_table.survival_probability(self.age, k)
            total = total + (self.v ** k) * survival
        return total

class Insurance(LifeProduct):
    """Common code for insurances paying a benefit at the END of the year of death."""

    def check_sum_assured(self, sum_assured):
        """Make sure the sum assured is a number and not negative."""
        if not isinstance(sum_assured, (int, float)):
            raise ValueError("Sum assured must be a number.")
        if sum_assured < 0:
            raise ValueError("Sum assured cannot be negative.")

    def death_benefit_epv(self, years):
        """EPV of a benefit of 1 paid at the end of the year of death,
        if death happens within the next 'years' years:

            sum of v^(k+1) * kp_x * q_(x+k)   for k = 0 to years-1
        """
        total = 0.0
        for k in range(years):
            survive_k_years = self.life_table.survival_probability(self.age, k)
            die_in_next_year = self.life_table.qx(self.age + k)
            discount = self.v ** (k + 1)
            total = total + discount * survive_k_years * die_in_next_year
        return total


class TermInsurance(Insurance):
    """Pays the sum assured at the end of the year of death, if death occurs within the term."""

    def term_insurance(self, term, sum_assured):
        """A_{x:n} (EPV of benefit) = sum_assured * sum of v^(k+1) * kp_x * q_(x+k), k = 0 to n-1."""
        self.check_term(term)
        self.check_sum_assured(sum_assured)
        return sum_assured * self.death_benefit_epv(term) 
    def net_annual_premium(self, term, sum_assured):
        """Level annual net premium, paid at the start of each year while alive.

        Equivalence principle:  P * a-due_{x:n} = EPV(benefits)
        so                      P = EPV(benefits) / a-due_{x:n}
        """
        self.check_term(term)
        self.check_sum_assured(sum_assured)

        epv_benefits = self.term_insurance(term, sum_assured)

        # Build an Annuity from the SAME table, age and interest rate
        annuity = Annuity(self.life_table, self.age, self.interest_rate)
        annuity_factor = annuity.term_annuity_due(term)

        return epv_benefits / annuity_factor


class WholeLifeInsurance(Insurance):
    """Pays the sum assured at the end of the year of death, whenever it occurs."""

    def whole_life_insurance(self, sum_assured):
        """A_x (EPV of benefit) = sum_assured * sum of v^(k+1) * kp_x * q_(x+k), to the end of the table."""
        self.check_sum_assured(sum_assured)
        years_left = self.life_table.max_age - self.age + 1
        return sum_assured * self.death_benefit_epv(years_left)