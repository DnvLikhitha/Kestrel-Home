# Submission Form — Kestrel Home Warranty Claim Review (Variant C)

**Candidate Name:** DNV Likhitha  
**Date Submitted:** 7 October 2026  
**Repository:** https://github.com/DnvLikhitha/Kestrel-Home.git  

---

### 1. What did you build, and what business outcome does it move? State the number and the money.
I built a logistic regression scoring model and decision service that prioritizes incoming warranty claims for human review to fit the investigation desk's fixed monthly capacity (40 claims/month).

In out-of-time backtesting on June 2026 claims, the model intercepted **12 of the 22 fraudulent claims**, saving **Rs 18,174** in prevented fraud while holding 26 genuine claims (**Rs 380 customer goodwill cost each**, totaling Rs 9,880). This generates a net return of **Rs 130 to Rs 220 per claim checked** (roughly **Rs 5,000 to Rs 9,000 net savings per month**), catching roughly **40% to 55%** of all fraud.

---

### 2. What score do you expect predictions.csv to get on the hidden outcomes, on which metric, and why that metric? Say how you estimated it.
- **Primary Metric:** **AUC-ROC** (and Precision@Top-40).
- **Expected Score:** **AUC of ~0.85** (plausible range: 0.75–0.90). Time-based backtests gave 0.88–0.89; I shaded it down to 0.85 because outlet history stops at 30 June 2026, and any outlets onboarded in Q3 have no prior fraud history in the training data.
- **Top 5% Precision:** Roughly **25%–30%** of the top 5% flagged claims will be true fraud, capturing 40%–55% of all fraud in the test set.
- **Why this metric & why not accuracy:** 96.9% of June claims were genuine. A trivial "approve all" baseline scores 96.9% accuracy while stopping Rs 0 in fraud. A model actively holding suspicious claims scores ~94%–95% accuracy because it holds genuine claims too. The board's 97% accuracy KPI cannot separate a working fraud model from an empty script.

---

### 3. How do you know it works? Sample size, how you checked, error rate, and the kind of case it gets wrong.
- **How checked:** Strict out-of-time chronological backtests (trained on historical data before 1 May 2026 to evaluate May–June; trained through May to evaluate June). Never random k-fold cross-validation.
- **Sample size:** The June backtest rests on only **22 confirmed fraud cases** (a second replay had 31), so performance figures must be treated as a range rather than exact guarantees.
- **Error rate & failure modes:**
  - *False Positives:* 26 of 38 reviewed claims in June were genuine (~68% false positive rate at the 5% cutoff), incurring Rs 380 goodwill cost each.
  - *False Negatives:* It misses fraud occurring at newly onboarded partner outlets where no prior confirmed-fraud history exists yet.
  - *Policy regime shifts:* A model trained before 1 May scored worse than random (AUC < 0.50) after the 1 May auto-approve rule change because it had never seen small, uninspected fraud.

---

### 4. Did you change, narrow, or push back on the client's ask? What, when, and why.
1. **Pushed back on the 97% Accuracy KPI:** Showed that paying all claims without inspection achieves 96.9% accuracy. Replaced it with Farhan’s metric: *Rupees of fraud stopped per claim checked, net of goodwill cost*.
2. **Pushed back on the "newer partners are the problem" assumption:** Proved that post-May fraud is concentrated in **7 specific outlets** (SP3160, SP3232, SP3318, SP3129, SP3319, SP3118, SP3286). The other ~38 new partners had only 1 fraud case in 153 claims. Blanketing all new partners would have alienated honest partners and captured less than a third of the net rupee return.
3. **Constrained review queue to 40 claims/month:** Capped the flagged queue to Farhan’s desk capacity (top ~5% by score) rather than arbitrary probability cutoffs.

---

### 5. What is wrong with what you are handing us, or with the data we handed you? Be specific: bugs, shortcuts, columns you did not trust, rows that looked wrong.
**Data issues:**
- **681 duplicate `claim_id`s:** Partners re-submit claims after a bounce; I kept only the first submission.
- **202 undecided cases:** Records with blank `is_fraud` in CRM were excluded rather than assumed to be genuine (which would dilute fraud signals).
- **Zoho legacy zeros:** Legacy Zoho CRM could not record blanks, converting unresolved cases to `0` prior to Oct 2025; documented as label noise.
- **Product serials (`product_serial`):** Manually typed by partners with heavy typos; zero signal for serial reuse or formatting anomalies.
- **Stale outlet history:** Outlets onboarded in Q3 have zero historical records in the training set.

**Model shortcuts:**
- Weighted post-1-May claims 3x during training based on heuristic operational judgement rather than hyperparameter tuning due to small sample size (22 cases).
- Excluded the Rs 260 customer contact cost because ops policy does not state that a desk review requires outbound contact.

---

### 6. What did you deliberately leave out, and why that rather than something else?
- **Gradient Boosting (LightGBM/XGBoost):** Gave a slightly higher backtest AUC (0.91 vs 0.89), but on 22 fraud cases that 0.02 delta was statistical noise. It delivered no incremental rupee gain, was harder to explain to investigators, and risked overfitting.
- **Serial Number Formatting & Reuse:** Discarded after tests showed partner typo noise overwhelmed any signal.
- **Hour of Day & Submission Time:** Pure spurious correlation with zero causal link to fraud.
- **Trailing 30-Day Outlet Volume:** Dropped so each incoming claim can be scored statelessly and independently without maintaining an external state store.
- **Blanket "New Partner" Rule:** Discarded to avoid penalizing 38 clean outlets.

---

### 7. Anything you built or found that nobody asked for?
1. **Identified the 7 rogue outlets:** Discovered that ~80% of flagged test-period claims sit with just 7 outlets. Recommending immediate revocation of their auto-approval privilege stops the bulk of fraud immediately without consuming the desk's 40 monthly review slots.
2. **Standalone, zero-dependency review service & plain-English UI:** Built a self-contained local web app and JSON endpoint (`POST /api/score`) running on pure Python standard library with no external frameworks or paid API keys, giving concrete operational reasons for human reviewers.
3. **Financial scenario model (`kestrel-evidence.xlsx`):** A parameterized workbook evaluating net rupee yield across varying goodwill costs and desk capacities.

---

### 8. What did you use AI for? Which tools and models, where they helped, where they wasted your time, what you threw away. Link your three-minute screen recording here.
- **Tools used:** Claude / Gemini for code scaffolding, data exploration scripts, and drafting the HTML/CSS interface.
- **Where they helped:** Rapidly building the Python HTTP server, formulating the ReportLab PDF script, and structuring data aggregations.
- **Where they wasted time & were wrong:**
  - The AI first generated contradictory reasons in the scoring service, incorrectly labeling authorized service centers (like SP3160) as "freelance technicians." I had to rewrite the explanation logic to use verified partner metadata.
  - An AI summary claimed a net return of Rs 309 per check; I caught the discrepancy against the workbook and corrected it to Rs 126.
- **Screen recording:** Included in repository / submission package (`kestrel home.mp4`).

---

### 9. Your Public Google Drive Link
*(Upload video and deliverables to your Google Drive and paste share link here if submitting via web form)*:  
(https://drive.google.com/file/d/124CBB0YqeEzL4CEnvTNkuSKc3EdkGdfW/view?usp=sharing)

---

### 10. Someone picks this up on Monday and you are unreachable. The three things they need to know.
1. **Retrain every month:** The fraud pattern changed overnight on 1 May 2026. A model that had not seen post-May data performed worse than random guessing. It must be retrained monthly, and it knows nothing about outlets onboarded after June.
2. **Audit the 7 outlets immediately:** Do not wait for the 40-claim desk queue. Revoke auto-approve privileges for SP3160, SP3232, SP3318, SP3129, SP3319, SP3118, and SP3286 to cut off ~80% of fraud at the source.
3. **Never judge the model on 97% accuracy:** Accuracy will punish the model for intercepting fraud. Track *rupees of fraud stopped per claim reviewed* (net of Rs 380 goodwill cost) as the board KPI.

---

### 11. Honest hours spent. One number.
**4 hours**

---

### 12. Github Repo Link
https://github.com/DnvLikhitha/Kestrel-Home.git

---

### 13. What does one prediction cost, and what would a month cost at Kestrel's volume (about 750 warranty claims a month)? Show the arithmetic. If you used no paid calls, say so.
- **Cost per prediction:** **Rs 0.00 ($0.00)**
- **Cost per month (750 claims):** **Rs 0.00 ($0.00)**

**Arithmetic:**  
The service uses a local logistic regression model running entirely on standard CPU within Python's built-in `http.server`. It makes **zero paid external API calls** (no OpenAI, Anthropic, or external API credits). Each inference executes in under 5 milliseconds on existing infrastructure, incurring zero incremental cloud or API cost.
