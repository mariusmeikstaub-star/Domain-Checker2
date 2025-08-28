import requests, time
from bs4 import BeautifulSoup

import re

def _parse_human_number(s: str):
    """
    Convert strings like '1,234', '1.234', '1.2k', '3,4 Mio', '2.5M', '1 234', '12.345,67' to float.
    Returns None if no number is found.
    """
    if s is None:
        return None
    txt = str(s).strip().lower()

    # Replace german words
    txt = txt.replace("mio", "m").replace("millionen", "m").replace("milliarden", "b")

    # Extract the first number-ish token
    # Keep digits, separators, and suffixes k/m/b
    m = re.search(r'([0-9][0-9\.,\s]*)([kmb])?', txt)
    if not m:
        # Sometimes it's like "1234 backlinks"
        m = re.search(r'([0-9]+)', txt)
        if not m:
            return None
        num = float(m.group(1))
        return num

    num_part = m.group(1)
    suffix = m.group(2)

    # Handle locales: if there are both '.' and ',', assume European format where '.' thousands, ',' decimal
    # If only one of them, decide best-effort
    if '.' in num_part and ',' in num_part:
        # European style like 12.345,67
        num_part = num_part.replace('.', '').replace(',', '.')
    else:
        # If there is a comma but not dot, could be thousands or decimal, assume thousands separator if there are 3 digits after
        # Fall back: remove spaces and commas as thousands
        # Keep one decimal separator as '.'
        # First replace spaces
        num_part = num_part.replace(' ', '')
        # If comma acts as thousands (e.g., 1,234), remove commas
        if re.search(r'\d,\d{3}(\D|$)', num_part):
            num_part = num_part.replace(',', '')
        # If comma seems decimal (e.g., 12,5), turn into dot
        elif re.search(r'\d+,\d+$', num_part):
            num_part = num_part.replace(',', '.')
        else:
            num_part = num_part.replace(',', '')

        # Remove stray thousands dots
        if re.search(r'\d\.\d{3}(\D|$)', num_part):
            num_part = num_part.replace('.', '')

    try:
        val = float(num_part)
    except Exception:
        # Last-chance digits only
        digits = re.findall(r'\d+', num_part)
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


_UA = {"User-Agent": "Mozilla/5.0 (compatible; DomainChecker/1.0; +https://example.com)"}

def _traffic_hypestat(domain: str):
    url = f"https://hypestat.com/info/{domain}"
    r = requests.get(url, headers=_UA, timeout=15)
    note = f"http={r.status_code}"
    if r.status_code != 200:
        return None, "hypestat", note
    soup = BeautifulSoup(r.text, "lxml")
    # Find label "Monthly Visits:"
    # Hypestat often has it inside text nodes; search by string and then fetch the next number
    label = soup.find(string=lambda t: t and "monthly visits" in t.lower())
    if not label:
        # Some pages have 'Monthly Unique Visitors' — try broader search
        label = soup.find(string=lambda t: t and "monthly" in t.lower() and "visit" in t.lower())
    if label:
        # Look nearby for a number
        parent = label.parent
        context = parent.get_text(" ", strip=True) if parent else str(label)
        # Try current node
        val = _parse_human_number(context)
        if val is None:
            # Try next sibling text
            sib = parent.find_next(string=True) if parent else None
            if sib:
                val = _parse_human_number(sib)
        if val is None:
            # Scan a few following nodes for a plausible number
            for el in (parent.next_elements if parent else []):
                txt = getattr(el, "get_text", lambda *a, **k: str(el))()
                val = _parse_human_number(txt)
                if val:
                    break
        if val:
            return float(val), "hypestat", note + ";ok"
    # If not found or n/a
    return None, "hypestat", note + ";no_data"

def _traffic_statshow(domain: str):
    url = f"https://www.statshow.com/www/{domain}"
    r = requests.get(url, headers=_UA, timeout=15)
    note = f"http={r.status_code}"
    if r.status_code != 200:
        return None, "statshow", note
    soup = BeautifulSoup(r.text, "lxml")
    # Look for "Daily Visitors:" then × 30
    label = soup.find(string=lambda t: t and "daily visitors" in t.lower())
    if not label:
        # sometimes "Visitors per day"
        label = soup.find(string=lambda t: t and "visitors per day" in t.lower())
    val = None
    if label:
        parent = label.parent
        context = parent.get_text(" ", strip=True) if parent else str(label)
        val = _parse_human_number(context)
        if val is None and parent:
            sib = parent.find_next(string=True)
            if sib:
                val = _parse_human_number(sib)
    if val:
        monthly = float(val) * 30.0
        return monthly, "statshow", note + ";ok"
    return None, "statshow", note + ";no_data"

def traffic_best_effort(domain: str, sleep_after: float = 1.0):
    """
    Return (monthly_visits or 0 if unknown, source, note)
    Tries Hypestat 'Monthly Visits:' first, then Statshow as fallback (Daily × 30).
    """
    domain = str(domain).strip().lower()

    # Try Hypestat
    try:
        v, src, note = _traffic_hypestat(domain)
        if isinstance(v, (int, float)) and v >= 0:
            time.sleep(max(0.0, float(sleep_after)))
            return int(round(v)), src, note
    except Exception as e:
        note = f"hypestat_error={type(e).__name__}"

    # Fallback Statshow
    try:
        v, src, note = _traffic_statshow(domain)
        if isinstance(v, (int, float)) and v >= 0:
            time.sleep(max(0.0, float(sleep_after)))
            return int(round(v)), src, note
    except Exception as e:
        note = f"statshow_error={type(e).__name__}"

    time.sleep(max(0.0, float(sleep_after)))
    return 0, "none", "no_data"
