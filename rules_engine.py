DISPOSABLE_EMAIL_DOMAINS = {"mailinator.com","10minutemail.com","tempmail.com"}
HIGH_AMOUNT_THRESHOLD = 20000  # $200 in cents

def is_disposable(email: str) -> bool:
    if not email or "@" not in email:
        return False
    return email.split("@")[-1].lower() in DISPOSABLE_EMAIL_DOMAINS

def score_rules(context: dict):
    """
    Return (score, reason) where score is 0..1
    """
    score, reasons = 0.0, []
    email = context.get("email")
    amount = context.get("amount", 0) or 0

    if not email:
        score += 0.2; reasons.append("missing_email")

    if is_disposable(email):
        score += 0.7; reasons.append("disposable_email")

    if amount >= HIGH_AMOUNT_THRESHOLD:
        score += 0.6; reasons.append("high_amount")

    score = min(1.0, score)
    if not reasons:
        reasons = ["no_rules_triggered"]
    return score, ",".join(reasons)
