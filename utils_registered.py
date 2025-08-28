import requests, time
from bs4 import BeautifulSoup  # not strictly needed here but kept for parity

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

def whois_is_registered(domain: str, sleep_after: float = 1.0):
    """
    Return (reg: True/False/None, source: str, note: str)
    RDAP first (rdap.org), then who.is fallback.
    """
    domain = str(domain).strip().lower()
    # --- RDAP ---
    try:
        rdap_url = f"https://rdap.org/domain/{domain}"
        r = requests.get(rdap_url, headers=_UA, timeout=12)
        note = f"http={r.status_code}"
        if r.status_code == 200:
            try:
                data = r.json()
            except Exception:
                data = {}
            # If JSON looks like a domain object (has ldhName or handle) => registered
            if isinstance(data, dict) and any(k in data for k in ("ldhName", "handle", "events", "entities")):
                time.sleep(max(0.0, float(sleep_after)))
                return True, "rdap", note
            # If not parseable but 200 => assume registered
            time.sleep(max(0.0, float(sleep_after)))
            return True, "rdap", note
        elif r.status_code in (404, 422):  # 404 Not found => likely unregistered
            time.sleep(max(0.0, float(sleep_after)))
            return False, "rdap", note
        else:
            # fallthrough
            pass
    except Exception as e:
        note = f"rdap_error={type(e).__name__}"

    # --- who.is fallback (HTML) ---
    try:
        url = f"https://who.is/whois/{domain}"
        r = requests.get(url, headers=_UA, timeout=12)
        note2 = f"http={r.status_code}"
        if r.status_code == 200:
            html = r.text.lower()
            # Heuristics: who.is shows "No match for" / "is available" when not registered
            if ("no match for" in html) or ("is available" in html) or ("not found" in html):
                time.sleep(max(0.0, float(sleep_after)))
                return False, "who.is", note2
            # If there is a registry expiry/creation date or registrar block -> registered
            if ("registrar" in html) or ("creation date" in html) or ("expiry date" in html) or ("updated date" in html):
                time.sleep(max(0.0, float(sleep_after)))
                return True, "who.is", note2
            # Unknown if nothing conclusive
            time.sleep(max(0.0, float(sleep_after)))
            return None, "who.is", note2
        else:
            time.sleep(max(0.0, float(sleep_after)))
            return None, "who.is", note2
    except Exception as e:
        time.sleep(max(0.0, float(sleep_after)))
        return None, "who.is", f"whois_error={type(e).__name__}"

def is_brand(domain: str) -> bool:
    """
    Very small heuristic: returns True if the SLD matches a known brand (nike etc.).
    """
    d = str(domain).strip().lower()
    if '.' in d:
        sld = d.split('.')[0]
    else:
        sld = d

    brands = {
        "nike","adidas","amazon","apple","google","microsoft","facebook","meta","tesla","samsung","netflix",
        "paypal","spotify","reddit","twitter","x","intel","amd","nvidia","bmw","mercedes","audi","shell",
        "coca","cocacola","coke","pepsi","mcdonalds","mcdonald","burgerking"
    }
    # direct match or startswith/endswith brand (avoid too many false positives)
    return (sld in brands) or any(sld.startswith(b) or sld.endswith(b) for b in brands)
