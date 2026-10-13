import csv


class LifeTable:
    """Reads a mortality table from a CSV file and answers survival questions."""

    def __init__(self, filename):
        self.filename = filename
        self.qx_values = {}      # dictionary: age -> qx, e.g. {30: 0.10, 31: 0.20}
        self.read_csv()
        self.min_age = min(self.qx_values)
        self.max_age = max(self.qx_values)

    # ---------- reading and validating the CSV ----------

    def read_csv(self):
        """Read the CSV file and store every age and qx."""
        try:
            with open(self.filename, newline="") as file:
                reader = csv.DictReader(file)
                self.check_columns(reader.fieldnames)
                for row in reader:
                    self.add_row(row)
        except FileNotFoundError:
            raise FileNotFoundError(f"Mortality file '{self.filename}' was not found.")

        if len(self.qx_values) == 0:
            raise ValueError("The mortality file contains no data rows.")

    def check_columns(self, column_names):
        """Make sure the header row has 'age' and 'qx'."""
        if column_names is None:
            raise ValueError("The mortality file is empty.")
        if "age" not in column_names:
            raise ValueError("The mortality file must contain an 'age' column.")
        if "qx" not in column_names:
            raise ValueError("The mortality file must contain a 'qx' column.")

    def add_row(self, row):
        """Check one row of the CSV and store it."""
        try:
            age = int(row["age"])
        except (ValueError, TypeError):
            raise ValueError(f"Age must be a whole number, but found '{row['age']}'.")

        try:
            qx = float(row["qx"])
        except (ValueError, TypeError):
            raise ValueError(f"qx must be a number for age {age}, but found '{row['qx']}'.")

        if qx < 0 or qx > 1:
            raise ValueError(f"qx must be between 0 and 1 for age {age}.")

        if age in self.qx_values:
            raise ValueError(f"Age {age} appears more than once in the mortality file.")

        self.qx_values[age] = qx

    # ---------- checking inputs to the methods ----------

    def check_age(self, age):
        """Make sure the age is a whole number inside the table."""
        if not isinstance(age, int):
            raise ValueError("Age must be a whole number.")
        if age not in self.qx_values:
            raise ValueError(f"Age {age} is outside the available mortality table.")

    # ---------- survival calculations ----------

    def qx(self, age):
        """Probability that a life aged x dies before reaching x+1."""
        self.check_age(age)
        return self.qx_values[age]

    def px(self, age):
        """Probability that a life aged x survives to x+1:  px = 1 - qx."""
        return 1 - self.qx(age)

    def survival_probability(self, age, years):
        """n_p_x = p_x * p_(x+1) * ... * p_(x+n-1)."""
        if not isinstance(years, int):
            raise ValueError("Years must be a whole number.")
        if years < 0:
            raise ValueError("Years cannot be negative.")

        probability = 1.0
        for k in range(years):
            probability = probability * self.px(age + k)
        return probability

    def death_probability(self, age, years):
        """Probability of dying within n years: 1 - n_p_x."""
        return 1 - self.survival_probability(age, years)

    def life_expectancy(self, age):
        """Curtate life expectancy: e_x = sum of k_p_x for k = 1, 2, 3, ..."""
        self.check_age(age)
        expectancy = 0.0
        for k in range(1, self.max_age - age + 2):
            expectancy = expectancy + self.survival_probability(age, k)
        return expectancy