"""قالب‌بندی اعداد"""


def format_number(value, decimals=0):
    try:
        num = float(value)
    except (TypeError, ValueError):
        return "0"
    if decimals == 0:
        formatted = f"{num:,.0f}"
    else:
        formatted = f"{num:,.{decimals}f}"
    return formatted.replace(",", "٬")


def parse_number(text):
    if not text:
        return 0
    text = str(text).replace("٬", "").replace(",", "").strip()
    try:
        return float(text)
    except ValueError:
        return 0
