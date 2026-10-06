"""
kestrel.py - Feature extraction, scoring logic, and plain-English risk explanation
for Kestrel Home Warranty Claim Review Service.
"""

import math
import os
import json

# Top 7 outlets with concentrated fraud under the post-May 1 auto-approve policy
HIGH_FRAUD_OUTLETS = {
    "SP3160": {"name": "SP3160 (Pune)", "fraud_cases": 10, "type": "Authorised Service Centre"},
    "SP3232": {"name": "SP3232 (Jaipur)", "fraud_cases": 7, "type": "Authorised Service Centre"},
    "SP3318": {"name": "SP3318 (Hubballi)", "fraud_cases": 6, "type": "Franchise"},
    "SP3129": {"name": "SP3129 (Chennai)", "fraud_cases": 4, "type": "Authorised Service Centre"},
    "SP3319": {"name": "SP3319 (Warangal)", "fraud_cases": 3, "type": "Franchise"},
    "SP3118": {"name": "SP3118 (Pune)", "fraud_cases": 2, "type": "Authorised Service Centre"},
    "SP3286": {"name": "SP3286 (Mysuru)", "fraud_cases": 2, "type": "Authorised Service Centre"}
}

# Product list prices for reference
PRODUCT_PRICES = {
    "KH-AF-01": 5999, "KH-AF-02": 7499, "KH-AF-03": 8999,
    "KH-MG-01": 3499, "KH-MG-02": 4999, "KH-MG-03": 6999,
    "KH-WP-01": 11999, "KH-WP-02": 14999, "KH-WP-03": 18999,
    "KH-RV-01": 21999, "KH-RV-02": 27999, "KH-RV-03": 34999,
    "KH-IC-01": 2999, "KH-IC-02": 3999, "KH-IC-03": 4999,
    "KH-CF-01": 2499, "KH-CF-02": 3299, "KH-CF-03": 4499,
    "KH-RH-01": 1999, "KH-RH-02": 2999, "KH-RH-03": 3999
}

REVIEW_THRESHOLD = 0.150  # Top ~5% of claims (desk capacity ~40/month)
WATCH_THRESHOLD = 0.040   # Next tier for monitoring

def score_claim(claim: dict) -> dict:
    """
    Scores a single warranty claim and returns human-readable risk drivers.
    Input format:
        partner_id: str (e.g. 'SP3160')
        sku: str (e.g. 'KH-AF-03')
        claim_amount_inr: float
        days_since_purchase: int
        partner_inspected: 'Y' or 'N'
        photo_attached: 'Y' or 'N'
        customer_prior_claims: int (optional, default 0)
    """
    partner_id = str(claim.get("partner_id", "")).strip().upper()
    sku = str(claim.get("sku", "")).strip().upper()
    amount = float(claim.get("claim_amount_inr", 0))
    days = int(claim.get("days_since_purchase", 0))
    inspected = str(claim.get("partner_inspected", "N")).strip().upper()
    photo = str(claim.get("photo_attached", "N")).strip().upper()
    prior_claims = int(claim.get("customer_prior_claims", 0))

    # Base log-odds: calibrated to base fraud rate ~3.1% in train set
    z = -4.10

    reasons_raising = []
    reasons_lowering = []

    # Factor 1: Outlet historical confirmed-fraud record
    if partner_id in HIGH_FRAUD_OUTLETS:
        info = HIGH_FRAUD_OUTLETS[partner_id]
        cases = info["fraud_cases"]
        ptype = info["type"]
        z += 3.40 + 0.15 * cases
        reasons_raising.append(
            f"Outlet {partner_id} ({ptype}) is one of 7 outlets with concentrated fraud ({cases} confirmed cases) since May 1"
        )
    else:
        z -= 0.60
        reasons_lowering.append(
            f"Outlet {partner_id} has a clean track record with no prior confirmed fraud clusters"
        )

    # Factor 2: Auto-approve loophole (< Rs 2,000 without inspection)
    if amount < 2000 and inspected == "N":
        z += 1.35
        reasons_raising.append(
            f"Uninspected claim under Rs 2,000 auto-approval threshold (Rs {amount:,.0f})"
        )
    elif inspected == "Y":
        z -= 1.10
        reasons_lowering.append(
            "Claim verified and signed off by partner inspection"
        )
    elif inspected == "N" and amount >= 2000:
        z += 0.40
        reasons_raising.append(
            f"Claim over Rs 2,000 submitted without mandatory inspection sign-off"
        )

    # Factor 3: Pre-May pattern - High value claim relative to product list price
    list_price = PRODUCT_PRICES.get(sku, 5000)
    price_ratio = amount / list_price if list_price > 0 else 0.5
    if price_ratio >= 0.85:
        z += 0.80
        reasons_raising.append(
            f"Claim amount (Rs {amount:,.0f}) is near full product list price (Rs {list_price:,.0f})"
        )
    elif price_ratio <= 0.35 and inspected == "Y":
        z -= 0.30
        reasons_lowering.append(
            f"Claim amount is modest ({price_ratio*100:.0f}% of product list price)"
        )

    # Factor 4: Customer history
    if prior_claims >= 2:
        z += 0.90 + 0.35 * (prior_claims - 2)
        reasons_raising.append(
            f"Customer has {prior_claims} prior warranty claims across products"
        )
    elif prior_claims == 0:
        z -= 0.20
        reasons_lowering.append(
            "First warranty claim for this customer"
        )

    # Factor 5: Photo evidence & purchase timing
    if photo == "N":
        z += 0.50
        reasons_raising.append("No photographic evidence attached to claim")
    else:
        reasons_lowering.append("Photographic evidence attached to claim")

    if days < 14:
        z += 0.40
        reasons_raising.append(f"Claim submitted very early ({days} days after purchase)")
    elif days > 330:
        z += 0.30
        reasons_raising.append(f"Claim submitted in warranty tail ({days} days after purchase)")

    # Logistic sigmoid
    score = 1.0 / (1.0 + math.exp(-z))
    score = round(score, 6)

    # Band allocation
    if score >= REVIEW_THRESHOLD:
        band = "REVIEW"
        action = "Hold for investigation desk"
    elif score >= WATCH_THRESHOLD:
        band = "WATCH"
        action = "Auto-pay, monitor partner outlet"
    else:
        band = "PAY"
        action = "Approve and pay"

    return {
        "score": score,
        "band": band,
        "action": action,
        "reasons_raising_risk": reasons_raising,
        "reasons_lowering_risk": reasons_lowering
    }
