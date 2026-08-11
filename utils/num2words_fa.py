"""تبدیل عدد به حروف فارسی (برای نمایش مبلغ به حروف)"""

YEKAN = ["", "یک", "دو", "سه", "چهار", "پنج", "شش", "هفت", "هشت", "نه"]
DAHGAN_2 = [
    "ده", "یازده", "دوازده", "سیزده", "چهارده", "پانزده",
    "شانزده", "هفده", "هجده", "نوزده",
]
DAHGAN = ["", "", "بیست", "سی", "چهل", "پنجاه", "شصت", "هفتاد", "هشتاد", "نود"]
SADGAN = [
    "", "صد", "دویست", "سیصد", "چهارصد", "پانصد",
    "ششصد", "هفتصد", "هشتصد", "نهصد",
]
SCALE = ["", "هزار", "میلیون", "میلیارد", "بیلیون", "بیلیارد"]


def _three_digit_to_words(n):
    """عدد سه‌رقمی (۰ تا ۹۹۹) را به حروف تبدیل می‌کند"""
    if n == 0:
        return ""
    parts = []
    sad = n // 100
    baghi = n % 100
    if sad:
        parts.append(SADGAN[sad])
    if baghi:
        if baghi < 10:
            parts.append(YEKAN[baghi])
        elif baghi < 20:
            parts.append(DAHGAN_2[baghi - 10])
        else:
            dah = baghi // 10
            yek = baghi % 10
            if yek:
                parts.append(DAHGAN[dah] + " و " + YEKAN[yek])
            else:
                parts.append(DAHGAN[dah])
    return " و ".join(parts)


def number_to_words_fa(value):
    """عدد صحیح را به حروف فارسی تبدیل می‌کند (مثال: 1250000 -> یک میلیون و دویست و پنجاه هزار)"""
    try:
        n = int(round(float(value)))
    except (TypeError, ValueError):
        return ""
    if n == 0:
        return "صفر"
    negative = n < 0
    n = abs(n)
    if n >= 10 ** (3 * len(SCALE)):
        return ""  # عدد بیش از حد بزرگ
    groups = []
    i = 0
    temp = n
    while temp > 0:
        groups.append(temp % 1000)
        temp //= 1000
        i += 1
    words = []
    for idx in range(len(groups) - 1, -1, -1):
        g = groups[idx]
        if g == 0:
            continue
        g_words = _three_digit_to_words(g)
        if idx > 0:
            g_words += " " + SCALE[idx]
        words.append(g_words)
    result = " و ".join(words)
    if negative:
        result = "منفی " + result
    return result


def amount_to_words_rial(value):
    """مبلغ را به حروف فارسی همراه با واحد ریال برمی‌گرداند"""
    words = number_to_words_fa(value)
    if not words:
        return ""
    if words == "صفر":
        return "صفر ریال"
    return f"{words} ریال"


def amount_to_words_toman(value):
    """مبلغ را به حروف فارسی همراه با واحد تومان برمی‌گرداند (مبلغ ریالی تقسیم بر ۱۰)"""
    try:
        toman = float(value) / 10
    except (TypeError, ValueError):
        return ""
    words = number_to_words_fa(toman)
    if not words:
        return ""
    if words == "صفر":
        return "صفر تومان"
    return f"{words} تومان"
