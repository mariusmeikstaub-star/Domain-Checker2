import requests, time
from bs4 import BeautifulSoup

from helpers import parse_human_number, UA_HEADER as _UA

def _backlinks_statshow(domain: str):
    url = f"https://www.statshow.com/www/{domain}"
    r = requests.get(url, headers=_UA, timeout=15)
    note = f"http={r.status_code}"
    if r.status_code != 200:
        return None, "statshow", note
    soup = BeautifulSoup(r.text, "lxml")
    label = soup.find(string=lambda t: t and "backlinks" in t.lower())
    if label:
        parent = label.parent
        context = parent.get_text(" ", strip=True) if parent else str(label)
        val = parse_human_number(context)
        if val is None and parent:
            sib = parent.find_next(string=True)
            if sib:
                val = parse_human_number(sib)
        if val is not None:
            return int(round(val)), "statshow", note + ";ok"
    return None, "statshow", note + ";no_data"

def _backlinks_hypestat(domain: str):
    url = f"https://hypestat.com/info/{domain}"
    r = requests.get(url, headers=_UA, timeout=15)
    note = f"http={r.status_code}"
    if r.status_code != 200:
        return None, "hypestat", note
    soup = BeautifulSoup(r.text, "lxml")
    label = soup.find(string=lambda t: t and "backlinks" in t.lower())
    if label:
        parent = label.parent
        context = parent.get_text(" ", strip=True) if parent else str(label)
        val = parse_human_number(context)
        if val is None and parent:
            sib = parent.find_next(string=True)
            if sib:
                val = parse_human_number(sib)
        if val is not None:
            return int(round(val)), "hypestat", note + ";ok"
    return None, "hypestat", note + ";no_data"

def backlinks_estimate(domain: str, sleep_after: float = 1.0):
    """
    Return (backlinks_total or 0, source, note)
    Tries Statshow first (tends to have a 'Backlinks:' line), then Hypestat.
    """
    domain = str(domain).strip().lower()

    # Statshow first
    try:
        v, src, note = _backlinks_statshow(domain)
        if isinstance(v, int) and v >= 0:
            time.sleep(max(0.0, float(sleep_after)))
            return v, src, note
    except Exception as e:
        note = f"statshow_error={type(e).__name__}"

    # Hypestat fallback
    try:
        v, src, note = _backlinks_hypestat(domain)
        if isinstance(v, int) and v >= 0:
            time.sleep(max(0.0, float(sleep_after)))
            return v, src, note
    except Exception as e:
        note = f"hypestat_error={type(e).__name__}"

    time.sleep(max(0.0, float(sleep_after)))
    return 0, "none", "no_data"
