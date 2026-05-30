# Program Evaluation — Pathways to Work (synthetic)

> Fictional youth employment program. Data from `generate_data.py`. This is a methods demonstration, not a real evaluation.

## 1. Headline (raw) result

- Program group employed at 6 months: **33.5%**
- Comparison group: **17.9%**
- Raw difference: **+15.6 pp** (chi-square p = 0.0000)

## 2. Baseline balance

Before trusting the raw number, check the groups are comparable:

|   treated |   age |   prior_unemployed_months |   has_year12 |
|----------:|------:|--------------------------:|-------------:|
|         0 | 20.47 |                      5.5  |         0.56 |
|         1 | 20.53 |                      5.71 |         0.55 |

## 3. Adjusted effect

Controlling for age, prior unemployment, Year 12 and region (logistic regression, average marginal effect), the program's estimated impact is **+15.7 percentage points** — the more defensible estimate of what the program actually contributed.

## 4. Who benefits most

| dimension   | group                |   lift_pp |    n |
|:------------|:---------------------|----------:|-----:|
| region      | Metro North          |      20.3 |  431 |
| ltu         | Long-term unemployed |      18.3 |  491 |
| region      | Regional             |      17.6 |  363 |
| has_year12  | 1                    |      16.4 |  833 |
| region      | Metro South          |      16.1 |  474 |
| ltu         | Shorter unemployment |      14.6 | 1009 |
| has_year12  | 0                    |      14.6 |  667 |
| region      | Remote               |       3.7 |  232 |

## 5. Cost-effectiveness

- Average cost per program participant: **$4,204**
- Estimated additional people employed: **117**
- **Cost per additional employment outcome: ~$26,810**

## Recommendation

The program shows a positive, statistically detectable effect that survives covariate adjustment. Impact is strongest for *Metro North*, suggesting tighter targeting could improve cost-effectiveness. Recommend continuation with a focus on the highest-lift subgroups and a longer follow-up window.
