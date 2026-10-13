from actuarial_life.life_table import LifeTable
from actuarial_life.products import Annuity, TermInsurance, WholeLifeInsurance

# ---------- Settings (change these to try other cases) ----------
age = 31
interest_rate = 0.05
term = 3
sum_assured = 1000000

# ---------- 1. Load the mortality table (the CSV is read ONCE, here) ----------
table = LifeTable("data/mortality.csv")

# ---------- 2. Survival and life expectancy ----------
print("--- Mortality ---")
print(f"5p{age} (survive 5 years):  {table.survival_probability(age, 5):.4f}")
print(f"Life expectancy e{age}:     {table.life_expectancy(age):.4f}")

# ---------- 3. Annuities (payments of 1 per year) ----------
annuity = Annuity(table, age, interest_rate)

print("\n--- Annuities (payment of 1 per year) ---")
print(f"{term}-year annuity-immediate: {annuity.term_annuity(term):.4f}")
print(f"Whole-life annuity-immediate:  {annuity.whole_life_annuity():.4f}")
print(f"Whole-life annuity-due:        {annuity.whole_life_annuity_due():.4f}")

# ---------- 4. Insurances (benefit paid at the end of the year of death) ----------
term_policy = TermInsurance(table, age, interest_rate)
whole_life_policy = WholeLifeInsurance(table, age, interest_rate)

print("\n--- Insurance (EPV of benefits) ---")
print(f"{term}-year term insurance, sum assured {sum_assured:,}: "
      f"{term_policy.term_insurance(term, sum_assured):,.2f}")
print(f"Whole-life insurance, sum assured {sum_assured:,}:       "
      f"{whole_life_policy.whole_life_insurance(sum_assured):,.2f}")

# ---------- 5. Net annual premium ----------
premium = term_policy.net_annual_premium(term, sum_assured)

print("\n--- Net premium ---")
print(f"Level annual net premium for the {term}-year term: {premium:,.2f}")

# ---------- 6. What happens with bad input ----------
print("\n--- Error handling ---")
try:
    term_policy.term_insurance(0, sum_assured)
except ValueError as error:
    print("Error caught:", error)