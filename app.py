
import os, io, time
import pandas as pd
import streamlit as st
from utils import whois_is_registered, traffic_best_effort, backlinks_estimate, is_brand

st.set_page_config(page_title="Domain Checker (stabil)", layout="wide")
st.title("Domain Checker – stabiler Lauf (RDAP + Traffic + Backlinks)")

with st.sidebar:
    st.header("Einstellungen")
    delay = st.slider("Sekunden Pause pro Anfrage", 0.5, 3.0, 1.0, 0.5)
    max_rows = st.number_input("Max. Domains prüfen (0 = alle)", min_value=0, value=0, step=100)
    min_monthly = st.number_input("Shortlist-Schwelle (Monthly Visits)", min_value=0, value=5000, step=500)
    st.markdown("---")
    st.write("CSV mit Domains (Spalte 'domain' oder 1. Spalte = Domain):")

up = st.file_uploader("Domainliste hochladen (.csv)", type=["csv"])

# Session-State, damit die App NICHT automatisch neu startet / in Schleife geht
if "do_run" not in st.session_state:
    st.session_state["do_run"] = False
if "last_results" not in st.session_state:
    st.session_state["last_results"] = None

domains = []
if up is not None:
    try:
        df_in = pd.read_csv(up)
    except Exception:
        up.seek(0)
        df_in = pd.read_csv(up, header=None, names=["domain"])
    colname = "domain" if "domain" in df_in.columns else df_in.columns[0]
    domains = [str(x).strip() for x in df_in[colname].dropna().tolist() if str(x).strip()]

c1, c2 = st.columns([1,1])
start = c1.button("🔍 Prüfung starten", type="primary", disabled=(not domains))
reset = c2.button("🔁 Zurücksetzen")

if start:
    st.session_state["do_run"] = True
    st.session_state["last_results"] = None
    st.rerun()

if reset:
    st.session_state["do_run"] = False
    st.session_state["last_results"] = None
    st.rerun()

if st.session_state["do_run"] and domains:
    if max_rows and max_rows > 0:
        domains = domains[:max_rows]

    st.write(f"{len(domains)} Domains werden geprüft…")
    prog = st.progress(0.0)
    out_rows = []
    hits_buffer = []
    status = st.empty()

    for i, domain in enumerate(domains, start=1):
        reg, who_src, who_note = whois_is_registered(domain, sleep_after=delay)

        # Only fetch traffic/backlinks for registered domains
        traf = 0
        traf_src = "none"
        traf_note = "skip_no_reg"
        bl = 0
        bl_src = "none"
        bl_note = "skip_no_reg"

        if reg:
            traf, traf_src, traf_note = traffic_best_effort(domain, sleep_after=delay)
            bl, bl_src, bl_note = backlinks_estimate(domain, sleep_after=delay)

        out_rows.append({
            "domain": domain,
            "is_registered": reg,
            "whois_source": who_src,
            "traffic_monthly_est": traf,
            "traffic_source": traf_src,
            "http_status_traffic_page": traf_note,
            "backlinks_total": bl,
            "backlinks_source": bl_src,
            "notes": f"whois={who_note} | traffic={traf_note} | backlinks={bl_note}",
            "tm_flag": bool(is_brand(domain)),
        })

        # Live-Ansicht (letzte 15)
        status.dataframe(pd.DataFrame(out_rows).tail(15))
        prog.progress(i/len(domains))

        if reg and int(traf) >= int(min_monthly):
            hits_buffer.append(out_rows[-1])

        if i % 25 == 0:
            df_tmp = pd.DataFrame(out_rows)
            df_tmp.to_csv("full_results.csv", index=False, encoding="utf-8-sig")

    # final speichern
    df_all = pd.DataFrame(out_rows)
    df_all.to_csv("full_results.csv", index=False, encoding="utf-8-sig")
    df_hits = pd.DataFrame(hits_buffer)
    df_hits.to_csv("hits_over_5000.csv", index=False, encoding="utf-8-sig")

    # Minimal-Export (robuste Typisierung, keine FutureWarnings)
    def _reg_to_text(v):
        return "ja" if v is True else ("nein" if v is False else "unbekannt")

    exp = pd.DataFrame({
        "Domain": df_all["domain"],
        "registriert": df_all["is_registered"].map(_reg_to_text),
        "Traffic": pd.to_numeric(df_all["traffic_monthly_est"], errors="coerce").fillna(0).astype(int),
        "Backlinks": pd.to_numeric(df_all["backlinks_total"], errors="coerce").fillna(0).astype(int),
    })
    exp.to_csv("export_min.csv", index=False, encoding="utf-8-sig")

    # Ergebnisse im State behalten, damit Downloads bei erneuter Ausführung NICHT neu rechnen
    st.session_state["last_results"] = {
        "full": df_all.to_dict(orient="list"),
        "hits": df_hits.to_dict(orient="list"),
        "exp": exp.to_dict(orient="list"),
    }
    st.session_state["do_run"] = False
    st.rerun()

# Anzeige + Downloads ohne erneuten Rechenlauf
if st.session_state["last_results"] is not None:
    st.success("Fertig. CSVs geschrieben: full_results.csv, hits_over_5000.csv, export_min.csv")
    st.markdown("---")
    st.subheader("Downloads")
    c1, c2, c3 = st.columns(3)
    for name, col in [("full_results.csv", c1), ("hits_over_5000.csv", c2), ("export_min.csv", c3)]:
        if os.path.exists(name):
            with open(name, "rb") as f:
                col.download_button(label=f"⬇️ {name}", data=f.read(), file_name=name, mime="text/csv")
