import random

def ml_score(context: dict):
    """
    Demo ML scorer: returns a probability 0..1 or None if not applicable.
    """
    amount = context.get("amount", 0) or 0
    if amount == 0:
        return None
    base = min(0.6, amount / 100000.0)  # larger amounts => slightly higher risk
    noise = random.uniform(-0.1, 0.1)
    return max(0.0, min(1.0, base + noise))
