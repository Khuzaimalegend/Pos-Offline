def format_rs(amount: float | int | None) -> str:
    try:
        if amount is None:
            amount = 0.0
        return f"Rs {float(amount):,.2f}"
    except Exception:
        return "Rs 0.00"
