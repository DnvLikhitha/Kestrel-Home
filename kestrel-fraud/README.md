# Kestrel warranty-claim risk service

Scores one warranty claim, says whether to hold it for the investigation desk, and explains why in plain English.
No paid API, no API key, no internet needed at run time.

## Run it (clean machine, Python 3.10+)
```
python3 -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python server.py                                        # then open http://localhost:8000
```
Change the port with `PORT=9000 python server.py`.

## Endpoint
`POST /api/score` with one claim as JSON:
```
curl -X POST localhost:8000/api/score -d '{"partner_id":"SP3160","sku":"KH-AF-03","claim_amount_inr":1450,
  "days_since_purchase":120,"partner_inspected":"N","photo_attached":"Y","customer_prior_claims":1}'
```
Required: partner_id, sku, claim_amount_inr, days_since_purchase, partner_inspected (Y/N), photo_attached (Y/N).
Optional: customer_prior_claims, inspector_note, submitted_at.
Returns `score`, `band` (REVIEW / WATCH / PAY), `action`, `reasons_raising_risk`, `reasons_lowering_risk`.
Bad input returns HTTP 400 with a readable message (never a stack trace). `GET /api/health` returns ok.

## Files
- `server.py` service + `static/index.html` the screen; `kestrel.py` features and reasons (shared with training)
- `model/` trained model, outlet fraud history, reference tables, review threshold
- `predictions.csv` scores for test_unlabelled.csv (2,252 rows)
- `train.py` retrain: put the four CSVs in `data/` (or pass a folder) and run `python train.py`

## Things to know
- Score is a ranking, not a probability. REVIEW = roughly the top 5% of claims (the desk's 40 a month).
- History stops at 30 Jun 2026. Outlets with no history get the company average. **Retrain monthly**: the fraud pattern changed on 1 May 2026 and a model that had not seen that was worse than random.
- Data is confidential (ops policy s10): do not commit `data/` or push this folder to a public repo.
