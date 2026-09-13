# BankAI — Credit Risk & Early Warning Intelligence Platform

An end-to-end AI platform simulating a bank's credit risk decision and early-warning workflow — from a synthetic-but-causally-realistic loan portfolio, through model comparison and calibration, to explainable per-customer decisions, behavioral early-warning detection, a REST API, a PostgreSQL schema and a bilingual React risk dashboard.

The same pipeline also runs against a **real** 30,000-customer bank dataset, so the numbers aren't only self-generated — including a fair-lending screen that flags a genuine disparate-impact signal on that real data.

```
✓ Probability of Default (PD) modeling
✓ Credit Risk Scoring (FICO-style scorecard)
✓ Explainable AI (SHAP)
✓ Early Warning Detection (behavioral trend re-scoring)
✓ Business Decision Engine (policy layer, separate from the model)
✓ Adverse Action Reason Codes (ECOA / Regulation B)
✓ Expected Credit Loss (IFRS 9 / CECL: PD × LGD × EAD)
✓ Macro Stress Testing (CCAR/DFAST-style scenario simulator)
✓ Fair Lending / Disparate-Impact Monitor
✓ Real-data benchmark (UCI Taiwanese credit-card book, 30k real customers)
✓ FastAPI REST API
✓ PostgreSQL (SQLAlchemy ORM)
✓ Model Monitoring (PSI / drift, calibration)
✓ Docker Compose
✓ React + TypeScript Risk Dashboard (Tailwind, Recharts)
✓ Bilingual UI — English / Turkish, locale-aware number formatting
```

## Why this exists

A bank doesn't just run `model.predict()`. Before approving a loan it moves data through a pipeline — customer data → risk score → PD → decision → explanation — and it keeps watching approved customers afterward for early signs of deteriorating risk. This project simulates that whole loop, not just the model in the middle of it.

```
                ┌───────────────┐
                │ Customer Data │   (synthetic 20k book  ·  real UCI 30k book —
                └───────┬───────┘    same pipeline, swappable adapter)
                        ↓
                ┌───────────────┐
                │   Feature     │
                │  Engineering  │
                        ↓
                ┌───────────────┐
                │ ML Risk Model │  (Logistic Regression / Random Forest / XGBoost
                └───────┬───────┘   — best of 3, isotonic-calibrated)
                        ↓
             ┌──────────┴──────────┐
             ↓                     ↓
     SHAP Explainability      PD → Credit Score
             ↓                     ↓
             └──────────┬──────────┘
                        ↓
                ┌───────────────┐
                │   Decision    │   (business policy: thresholds, pricing —
                │    Engine     │    kept separate from the ML model)
                └───────┬───────┘
                        ↓
             ┌──────────┴──────────┐
             ↓                     ↓
    Adverse Action Reasons   Expected Loss (PD×LGD×EAD)
     (ECOA / Reg B, on           + Stress Testing
      MANUAL_REVIEW/REJECT)      + Fair Lending Monitor
             ↓                     ↓
             └──────────┬──────────┘
                        ↓
                ┌───────────────┐
                │   FastAPI     │───→ PostgreSQL (customers, loans, transactions,
                └───────┬───────┘     credit_history, risk_predictions,
                        ↓             risk_alerts, model_versions)
                ┌───────────────┐
                │   Dashboard   │   (React + TypeScript SPA, EN/TR — control
                └───────────────┘    center, customer 360, early-warning alerts,
                                      model monitoring, stress test lab,
                                      real-dataset benchmark)
```

A second, standing loop runs over the existing portfolio: each customer's 12-month behavioral history (utilization, balance, withdrawals, late payments) is re-scored by the **same model** at two points in time. A real transition between risk buckets — not just a threshold breach — triggers an early-warning alert.

## Screenshots

**Risk Control Center** — portfolio KPIs, live risk distribution, unresolved early-warning alerts.

![Risk Control Center](docs/screenshots/control_center.svg)

**Live Risk Simulator** — a new application scored end to end, with the SHAP drivers behind the number.

![Live Risk Simulator with SHAP explanation](docs/screenshots/customer_360_shap.svg)

**Real Dataset Benchmark** — the same pipeline on 30,000 real customers, and the fair-lending finding it surfaced.

![Real dataset benchmark and fair lending screen](docs/screenshots/real_dataset_fairness.svg)

## Example: `POST /predict-risk`

```json
{
  "age": 34, "occupation": "Engineer", "income": 85000,
  "employment_years": 3, "credit_history_years": 6,
  "num_existing_loans": 2, "num_credit_inquiries_6m": 3,
  "total_debt": 310000, "monthly_payment": 9800,
  "credit_utilization": 0.72, "num_late_payments": 2,
  "account_balance": 42000, "transaction_intensity": 35,
  "loan_amount": 250000
}
```

```json
{
  "risk_score": 738,
  "probability_of_default": 0.081,
  "risk_level": "MEDIUM",
  "decision": "MANUAL_REVIEW",
  "suggested_interest_rate": 0.0427,
  "approved_amount": 250000.0,
  "key_risk_drivers": [
    { "feature": "Debt / Income Ratio", "contribution": 0.21 },
    { "feature": "Credit Utilization", "contribution": 0.16 },
    { "feature": "Late Payments", "contribution": 0.13 },
    { "feature": "Employment Duration", "contribution": 0.07 },
    { "feature": "Account Balance", "contribution": -0.04 }
  ],
  "reason_codes": [
    "Debt-to-income ratio is too high",
    "Proportion of revolving balances to credit limits is too high"
  ]
}
```

`reason_codes` is empty on `APPROVE` and only populated on `MANUAL_REVIEW`/`REJECT` — mirroring how adverse action notices actually work.

(Actual numbers vary run-to-run — see `artifacts/model_metrics.json` for the exact trained model's figures.)

## Early Warning example

```
January   Credit utilization: 32%
February  Credit utilization: 41%
March     Credit utilization: 58%
April     Credit utilization: 71%
```

```json
{
  "customer_id": 18472,
  "previous_risk_level": "LOW",
  "current_risk_level": "HIGH",
  "signals": [
    "Credit utilization increased 39% in last 2 months",
    "Account balance decreased 22%",
    "1 new late payment(s) recorded",
    "Cash withdrawal frequency +42%"
  ],
  "recommended_action": "Immediate customer risk review"
}
```

This isn't a threshold rule on one field — it's the same PD model scored at two points in the customer's 12-month history, so "risk increased" means the model's own estimate moved between risk buckets.

## Real-data benchmark (not just synthetic)

The synthetic portfolio makes for a clean demo, but a model that has only ever
seen data you generated yourself proves nothing. The same pipeline therefore
also trains on a **real** dataset — the UCI *Default of Credit Card Clients*
book (30,000 real customers of a Taiwanese bank, April–September 2005, with
genuine default outcomes and six months of real billing/payment history):

```bash
python -m src.models.train --dataset uci     # trains on the real data
python -m scripts.analyze_real_dataset       # scores the book, runs fairness + early warning
```

Only the data adapter (`src/datasets/uci_credit.py`) is new — the training
core, decision engine, expected-loss, fair-lending and early-warning modules
are imported unchanged. That dataset was chosen specifically because it is one
of the few public credit datasets carrying a real *monthly* behavioral history,
which is what the early-warning engine needs: it rebuilds every feature as it
looked two months earlier (`build_customers(as_of_index=...)`) and re-scores,
surfacing 6,175 genuine risk escalations across the book.

The dashboard's **Real Dataset** page shows the result side by side with the
synthetic one:

| | Synthetic | Real (UCI) |
|---|---|---|
| Champion model | logistic_regression | **xgboost** |
| ROC-AUC | 0.928 | **0.779** |
| Gini | 0.855 | **0.559** |
| KS | 0.730 | **0.433** |
| Base default rate | 7.1% | 22.1% |

Three things worth saying out loud about that table:

- **The gap is the point.** 0.78 AUC is a normal, publishable result for this
  dataset; 0.93 on synthetic data is the model rediscovering the formula that
  generated it. Reporting only the synthetic number would be dishonest.
- **The winner changes.** Logistic regression wins on synthetic data because
  the generator is mostly linear in the log-odds. On the real book the gradient
  boosted trees win — real repayment behavior carries interactions a linear
  scorecard can't see.
- **Calibration holds up.** On the real portfolio the model's average PD lands
  at 22.4% against a 22.1% actual default rate.

### What the fair-lending screen found on real data

The real dataset carries genuine protected attributes (sex, marital status,
education). They are **excluded from the feature set** — ECOA/Regulation B
prohibits basing a credit decision on sex or marital status — and used only by
the fairness monitor. Running the four-fifths screen over the scored book:

| Attribute | Result |
|---|---|
| Sex | Male 0.910 vs Female 1.000 — **pass** |
| Marital status | Married 0.979, Single 1.000 — **pass** |
| Education | High School **0.746 — FLAGGED**, University 0.838, Graduate School 1.000 |

The model never sees education, yet high-school-educated applicants are
approved at 75% the rate of graduate-educated ones. That is a textbook
**proxy effect** leaking in through correlated behavioral features, and in a
real bank it is exactly the finding that would open a compliance review rather
than ship. A screen that never fires on real data isn't a screen.

## Data science pipeline

`src/data/generate_synthetic_data.py` builds a **causally-structured** synthetic portfolio (not random noise): default probability is a logistic function of debt-to-income, utilization, late-payment history, credit tenure, recent inquiries and an interaction term, calibrated to a ~7% base default rate. ~18% of customers are seeded with a deteriorating last-3-month trend so the early-warning engine has genuine signal to find, and ~10% with an improving trend.

`src/features/engineering.py` joins static customer attributes with point-in-time behavioral deltas (utilization/balance/withdrawal changes over 30/60/90 days) derived from the monthly `credit_history` table — the same function is re-run at different `as_of_month_index` values to reconstruct "3 months ago" for early-warning re-scoring.

`src/models/train.py` trains and compares **Logistic Regression, Random Forest and XGBoost**, then isotonic-calibrates the ROC-AUC champion (on the synthetic book calibration cuts the Brier score from 0.104 to 0.039 — see `artifacts/model_metrics.json`). The training core is dataset-agnostic: it takes a feature spec and a labeled frame, which is how `--dataset uci` reuses it unchanged. Evaluation goes beyond accuracy:

| Metric | Why it matters for credit risk |
|---|---|
| ROC-AUC / Gini | Overall rank-ordering power (Gini = 2×AUC−1, the industry-standard credit scorecard metric) |
| PR-AUC | More informative than ROC-AUC under class imbalance (~7% default rate) |
| KS Statistic | Classic scorecard metric: max separation between good/bad cumulative distributions |
| Precision / Recall / F1 | Cost of missed defaults vs. cost of rejecting good customers |
| Brier Score | Calibration quality — are stated probabilities trustworthy, not just rank-ordering |
| Calibration Curve | Visual check: does "10% PD" actually default ~10% of the time |

## Explainable AI

`src/explainability/shap_explainer.py` wraps the champion model with a model-agnostic SHAP `PermutationExplainer`, so every prediction comes with a ranked, human-readable list of what pushed risk up or down — the same explanation surfaces in `/predict-risk`, `/credit-decision` and the dashboard's Customer 360 page.

One detail that is easy to get wrong and worth calling out: the explainer runs against the **calibrated** pipeline, not the raw model underneath it. The base estimator is fit with `class_weight="balanced"`, which shifts its probabilities onto a different scale entirely — explaining that model would have produced drivers that summed to a number nowhere near the PD actually shown to the user. Attributing on the calibrated pipeline keeps `base_value + Σcontributions` equal to the reported probability of default.

## Decision engine

`src/decision/engine.py` is intentionally **not** part of the model. Credit policy (approve/review/reject thresholds, risk-based pricing, exposure caps) changes on a business cadence, needs to be auditable, and shouldn't require retraining a model to adjust.

Thresholds live in a `CreditPolicy` rather than as module constants, because a cut-off only means something relative to a portfolio's base default rate — the synthetic book defaults at ~7% and the real UCI card book at ~22%, so one set of numbers cannot serve both:

```python
DEFAULT_POLICY = CreditPolicy(approve_below=0.05, review_below=0.12)   # synthetic book
UCI_POLICY     = CreditPolicy(approve_below=0.15, review_below=0.30)   # real card book

if   pd < policy.approve_below: decision = "APPROVE"
elif pd < policy.review_below:  decision = "MANUAL_REVIEW"
else:                           decision = "REJECT"
```

## Model monitoring

`src/monitoring/drift.py` computes **Population Stability Index (PSI)** per feature against the training-time reference distribution — the dashboard's Model Monitoring page surfaces PSI, drift severity, calibration curves and the live risk-level distribution, closing the loop from "trained a model" to "watching it in production."

## Regulatory & risk management

A model that only outputs a probability isn't deployable at a bank. Four pieces close that gap:

**Adverse Action Reason Codes** (`src/decision/reason_codes.py`) — U.S. lenders must tell a declined applicant *why* under ECOA/Regulation B (12 CFR 1002.9). Rather than maintaining a separate rule engine, the reasons are derived straight from the SHAP drivers that increased *this* applicant's PD the most, translated into standard notice language. `age` and `occupation` are hard-excluded from ever appearing on a notice — one is a protected characteristic under ECOA, the other a plausible proxy for one.

**Expected Credit Loss** (`src/risk/expected_loss.py`) — IFRS 9 / CECL-style provisioning: `EL = PD × LGD × EAD`, with LGD defaulted to Basel's 45% Foundation-IRB senior-unsecured-retail assumption. Surfaced as a portfolio KPI on the Model Monitoring page.

**Stress Testing** (`src/risk/stress_test.py`, dashboard → *Stress Test Lab*) — a CCAR/DFAST-style macro scenario: an unemployment shock and a rate shock push utilization up, income down and payments up on the sampled portfolio, which is then **re-scored with the exact same production model** — not a separate stress model — to compare baseline vs. stressed risk distribution and expected loss.

**Fair Lending Monitor** (`src/monitoring/fairness.py`, dashboard → *Model Monitoring* and *Real Dataset*) — a disparate-impact screen using the EEOC/OFCCP four-fifths rule: any group approved less than 80% as often as the reference group is flagged for review. On the synthetic book `occupation` stands in as a demonstration segment; on the real UCI book it runs against genuine protected attributes (sex, marital status, education) and **finds something** — see the section above.

Two details the implementation gets right that a naive version doesn't:

- **The reference group needs a real sample.** UGESP notes the four-fifths rule is unreliable on small samples. Letting whichever tiny segment happens to have the highest approval rate become the yardstick makes every other group look adverse — on the real dataset a 123-person segment initially flagged three groups spuriously. Groups under `MIN_GROUP_SIZE` (500) are now reported but cannot become the reference, and are marked `insufficient_sample` rather than flagged.
- **A flag is not a verdict.** It opens a compliance investigation; it is never grounds for automated action, and the protected attributes are excluded from the model precisely so that anything the screen catches is a *proxy* effect worth investigating.

## Project layout

```
src/
  data/            synthetic data generator
  datasets/        real-data adapters (UCI credit-card book)
  features/        point-in-time feature engineering
  models/          train/evaluate/inference/scoring
  explainability/  SHAP wrapper
  decision/        business rule engine + adverse action reason codes
  early_warning/   behavioral re-scoring & alert detection
  risk/            expected loss (IFRS9/CECL) + macro stress testing
  monitoring/      PSI / drift + fair lending disparate-impact monitor
  db/              SQLAlchemy models, session, seeding
api/               FastAPI app + routers
frontend/          React + TypeScript SPA (Vite, Tailwind CSS, Recharts)
  src/api/         typed REST client
  src/components/  top nav, design-system primitives (ui.tsx), badges, SHAP chart
  src/i18n/        English/Turkish translations + locale provider
  src/pages/       Control Center, Customer 360, Alerts, Monitoring, Simulator,
                   Stress Test Lab, Real Dataset
scripts/           run_pipeline.py (synthetic: generate → train → seed)
                   analyze_real_dataset.py (real book: score → fairness → early warning)
tests/             pytest suite
```

> `dashboard/` also contains an earlier Streamlit prototype of the same UI, kept for quick local iteration without a Node toolchain (`streamlit run dashboard/Home.py`) — `frontend/` is the primary, production-styled dashboard.

## Database schema

`customers · loans · transactions · credit_history · risk_predictions · risk_alerts · model_versions` — see `src/db/models.py`.

## API

```
POST /predict-risk               Score a new applicant (no DB record needed) + reason codes
GET  /customer/{id}              Customer profile + latest risk snapshot
GET  /customer/{id}/risk-history Monthly utilization/balance trend
GET  /alerts                     Early-warning alerts (filter by risk_level, resolved)
POST /credit-decision            Full decision for an existing customer + reason codes
GET  /model/metrics              Model comparison, champion, calibration curve
GET  /model/monitoring           PSI / drift / risk distribution
GET  /portfolio/summary          Dashboard KPIs
GET  /portfolio/expected-loss    Portfolio Expected Credit Loss (IFRS 9 / CECL)
POST /portfolio/stress-test      Macro scenario simulation (CCAR/DFAST-style)
GET  /portfolio/fairness         Fair lending disparate-impact screen
GET  /real-dataset/provenance    Real dataset source, citation, excluded attributes
GET  /real-dataset/metrics       Real vs. synthetic model performance
GET  /real-dataset/summary       Real portfolio KPIs + expected loss
GET  /real-dataset/fairness      Fair lending screen on real protected attributes
GET  /real-dataset/alerts        Early-warning alerts from real behavioral history
```

Interactive docs at `http://localhost:8000/docs` once the API is running.

## Running it

**Option A — Docker Compose (Postgres, matches the architecture diagram):**

```bash
docker compose up --build
```

This starts Postgres, runs the pipeline (generate data → train → seed) as a one-off job, then starts the API on `:8000` and the React dashboard (served as a static build via `serve`) on `:4173`.

**Option B — local dev (SQLite, zero setup, hot-reload on both sides):**

```bash
# backend
python -m venv .venv && source .venv/Scripts/activate   # or .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
python -m scripts.run_pipeline
uvicorn api.main:app --reload

# frontend, in a second terminal
cd frontend
npm install
npm run dev
```

Then open `http://localhost:5173` for the dashboard or `http://localhost:8000/docs` for the API. The frontend reads its API URL from `frontend/.env` (`VITE_API_BASE_URL`, defaults to `http://localhost:8000`).

To view the dashboard from another device (e.g. a phone) on the same network, Vite's dev server already binds to all interfaces (`server.host: true` in `vite.config.ts`) — open the `Network:` URL it prints (e.g. `http://<your-machine-ip>:5173`) from that device.

### Tests

```bash
pytest            # 23 tests: decision engine, scoring, reason codes, expected loss,
                  # stress shocks, fairness screen, UCI adapter, API contract
cd frontend && npx tsc -b --noEmit   # frontend type check
```

The fairness tests are worth a look — one of them pins the small-sample rule by
asserting that a 3-person group with a 100% approval rate cannot become the
reference that flags everyone else.

## Design system & localization

The dashboard is built against a token-driven design system defined in the
`@theme` block of `frontend/src/index.css`: white canvas, black pill CTAs, a
canary-yellow brand mark reserved for the wordmark and tag chips, and pastel
feature cards (yellow / coral / rose / teal) carrying the KPI tiles. Radii, type
scale and elevation all resolve from those tokens — components never hard-code a
one-off value. `frontend/src/components/ui.tsx` holds the primitives (Button,
Card, FeatureCard, StatCard, Chip, PillTab, Table, Callout).

Chart colors come from the same palette rather than a separate viz theme: risk
severity reads as an ordered ramp — teal → yellow → coral → deep wine — and SHAP
bars use teal for risk-reducing and coral for risk-increasing contributions.

Type is set in Roobert PRO where available, falling back to **Plus Jakarta
Sans** (the closest freely available match for its geometric, slightly rounded
character) since Roobert is a commercial licence.

The whole UI ships in **English and Turkish**. `frontend/src/i18n/` holds the
translation tables and a provider that persists the choice to `localStorage` and
picks up the browser language on first load. Numbers, percentages and dates run
through `Intl` with the active locale, so Turkish renders `20.000` and `%7,05`
where English renders `20,000` and `7.05%`. Switch languages from the top-right
toggle.

## Stack

`Python · scikit-learn · XGBoost · SHAP · FastAPI · SQLAlchemy · PostgreSQL · React · TypeScript · Tailwind CSS · Recharts · Docker`

## What a bank risk manager sees that a generic Kaggle project doesn't

- **Reasons, not just a number** — adverse action notices in the applicant's actual approval/decline flow, generated from the model's own explanation.
- **Money, not just probability** — expected loss in currency, so a risk-distribution shift translates into a provisioning number a CFO would recognize.
- **"What if," not just "what is"** — a macro stress scenario re-run through the *live* production model, the same exercise CCAR/DFAST asks large banks to run annually.
- **Compliance, not just accuracy** — a disparate-impact check sitting next to ROC-AUC on the same monitoring page, because a model that's accurate but discriminatory doesn't ship.
- **Real data, and the honest number that comes with it** — 0.78 AUC on a real portfolio reported next to the flattering 0.93 synthetic one, rather than only the number that looks good.

## Roadmap / not built yet

Ideas that would extend this further, deliberately left out of v1 to keep scope honest:

- **Champion/Challenger promotion workflow** — automatically compare a newly trained challenger against the live champion on a holdout set and require a signed-off threshold before promoting (`model_versions.is_active` already supports multiple versions).
- **Vintage/cohort analysis** — default-rate curves by origination month, the classic credit-risk view of how a lending cohort ages.
- **Batch scoring** — CSV upload → bulk `/predict-risk` → downloadable decisions, for loan-officer workflows that aren't one-applicant-at-a-time.
- **Webhook/notification hook on early-warning alerts** — push HIGH/CRITICAL transitions to a real channel (email/Slack) instead of only appearing in the dashboard.

---
🤖 Built with [Claude Code](https://claude.com/claude-code)
