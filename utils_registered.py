import requests, time

from helpers import UA_HEADER as _UA

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
