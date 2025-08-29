import re

UA_HEADER = {"User-Agent": "Mozilla/5.0 (compatible; DomainChecker/1.0; +https://example.com)"}

def parse_human_number(s: str):
    """Convert strings like '1,234', '1.234', '1.2k', '3,4 Mio',
    '2.5M', '1 234', '12.345,67' to float. Returns None if no number is found."""
    if s is None:
        return None
    txt = str(s).strip().lower()
    txt = txt.replace("mio", "m").replace("millionen", "m").replace("milliarden", "b")
    m = re.search(r"([0-9][0-9\.,\s]*)([kmb])?", txt)
    if not m:
        m = re.search(r"([0-9]+)", txt)
        if not m:
            return None
        return float(m.group(1))
    num_part, suffix = m.group(1), m.group(2)
    if '.' in num_part and ',' in num_part:
        num_part = num_part.replace('.', '').replace(',', '.')
    else:
        num_part = num_part.replace(' ', '')
        if re.search(r"\d,\d{3}(\D|$)", num_part):
            num_part = num_part.replace(',', '')
        elif re.search(r"\d+,\d+$", num_part):
            num_part = num_part.replace(',', '.')
        else:
            num_part = num_part.replace(',', '')
        if re.search(r"\d\.\d{3}(\D|$)", num_part):
            num_part = num_part.replace('.', '')
    try:
        val = float(num_part)
    except Exception:
        digits = re.findall(r"\d+", num_part)
        if not digits:
            return None
        val = float(''.join(digits))
    if suffix == 'k':
        val *= 1_000
    elif suffix == 'm':
        val *= 1_000_000
    elif suffix == 'b':
        val *= 1_000_000_000
    return float(val)
