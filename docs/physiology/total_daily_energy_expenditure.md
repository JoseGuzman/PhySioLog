# Total Daily Energy Expenditure (TDEE) Calculation

This document explains how **Total Daily Energy Expenditure (TDEE)** is estimated using the **Mifflin-St Jeor equation** combined with an **activity multiplier** [1].

This formula calculates the **estimated daily calorie expenditure** based on body characteristics and physical activity level.

---

# 1. Overview

The Total Daily Energy Expenditure (**TDEE**) represents the **total number of calories the body burns in a day**.

It comprises the following physiological components:

* Basal Metabolic Rate (BMR): Energy required for basic physiological functions.
* Thermic Effect of Food (TEF): Energy used to digest and process food.
* Non-Exercise Activity Thermogenesis (NEAT): Energy spent during daily movement [3].
* Exercise Activity Thermogenesis (EAT): Energy spent during structured exercise.

In practice, **Basal Metabolic Rate (BMR)** is estimated from population variables (weight, height, age, and sex), then multiplied by an **Activity Factor (AF)** to approximate total daily expenditure [2].

$$
\text{TDEE} = \text{BMR} \times \text{AF}
$$

BMR is computed from population variables using the following equations [1]:

For males:
$$
\text{BMR} = (10 \times \text{Weight} + 6.25\times\text{Height} - 5 \times\text{Age} + 5)
$$

For females:

$$
\text{BMR} = (10 \times \text{Weight} + 6.25\times\text{Height} - 5 \times\text{Age} - 161)
$$

Units:

| Variable | Unit  |
| -------- | ----- |
| Weight   | kg    |
| Height   | cm    |
| Age      | years |

These equations estimate the **energy required by the body at rest**.

---

# 2. Activity Factor: an Activity Multiplier

To convert BMR into TDEE, the formula multiplies the result by an **activity factor**.

| Activity Level              | Multiplier |
| --------------------------- | ---------- |
| Sedentary (little exercise) | 1.2        |
| Light activity              | 1.375      |
| Moderate exercise           | 1.55       |
| High activity               | 1.725      |
| Very high activity          | 1.9        |

This multiplier approximates the combined effect of:

* daily movement
* structured exercise
* thermic effect of food

---

# 3. Example Calculation

Assume:

| Variable        | Value    |
| --------------- | -------- |
| Weight          | 70 kg    |
| Height          | 175 cm   |
| Age             | 30 years |
| Sex             | Male     |
| Activity factor | 1.55     |

### Step 1 - BMR calculation

$$
\text{BMR} = 10×70 + 6.25×175 − 5×30 + 5 = 1648.75
$$

The result is in kcal/day.

### Step 2 — TDEE

$$
\text{TDEE} = 1648.75 \times 1.55 \approx 2556
$$

This means the person would need approximately **2556 kcal per day to maintain body weight**.

---

# 4. Interpretation

TDEE estimates are used to design nutrition strategies:

| Goal               | Strategy        |
| ------------------ | --------------- |
| Weight maintenance | Calories ≈ TDEE |
| Fat loss           | Calories < TDEE |
| Weight gain        | Calories > TDEE |

Typical adjustments:

| Goal      | Adjustment        |
| --------- | ----------------- |
| Fat loss  | −300 to −500 kcal |
| Lean gain | +200 to +300 kcal |

---

# 5. Limitations

TDEE calculations are **population-based estimates** and can vary between individuals due to:

* metabolic adaptations
* body composition differences
* hormonal factors
* measurement error in activity level
* day-to-day energy expenditure variation

Typical estimation error ranges from **±10–20%**.

---

# 6. Key Takeaways

* TDEE estimates total daily energy expenditure.
* The **Mifflin-St Jeor BMR equation** provides a population-based estimate [1].
* Activity level is incorporated using a **multiplicative activity factor**.
* TDEE calculations provide **useful estimates**, but real-world energy expenditure varies.

---

# References

1. Mifflin MD, St Jeor ST, Hill LA, Scott BJ, Daugherty SA, Koh YO.  
   *A new predictive equation for resting energy expenditure in healthy individuals.*  
   **Am J Clin Nutr.** 1990;51(2):241-247.  
   [PubMed](https://pubmed.ncbi.nlm.nih.gov/2305711/) · [DOI](https://doi.org/10.1093/ajcn/51.2.241)

2. Frankenfield D, Roth-Yousey L, Compher C.  
   *Comparison of predictive equations for resting metabolic rate in healthy nonobese and obese adults: a systematic review.*  
   **J Am Diet Assoc.** 2005;105(5):775-789.  
   [PubMed](https://pubmed.ncbi.nlm.nih.gov/15883556/) · [DOI](https://doi.org/10.1016/j.jada.2005.02.005)

3. Levine JA.  
   *Non-exercise activity thermogenesis (NEAT).*  
   **Best Pract Res Clin Endocrinol Metab.** 2002;16(4):679-702.  
   [PubMed](https://pubmed.ncbi.nlm.nih.gov/12468415/) · [DOI](https://doi.org/10.1053/beem.2002.0221)
