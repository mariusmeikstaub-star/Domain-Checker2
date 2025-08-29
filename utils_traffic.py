import requests, time
from bs4 import BeautifulSoup

from helpers import parse_human_number, UA_HEADER as _UA

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
        val = parse_human_number(context)
        if val is None:
            # Try next sibling text
            sib = parent.find_next(string=True) if parent else None
            if sib:
                val = parse_human_number(sib)
        if val is None:
            # Scan a few following nodes for a plausible number
            for el in (parent.next_elements if parent else []):
                txt = getattr(el, "get_text", lambda *a, **k: str(el))()
                val = parse_human_number(txt)
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
        val = parse_human_number(context)
        if val is None and parent:
            sib = parent.find_next(string=True)
            if sib:
                val = parse_human_number(sib)
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
