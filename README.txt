# Domain Parking – Safe Online Checker (No API, Live View)

Dieses Tool prüft große Domainlisten **ohne API & ohne Kosten**:
1) **WHOIS via Website-Scraping** (who.is) → Ist die Domain registriert?
2) **Traffic-Schätzung via Website-Scraping** (Hypestat) → Nur wenn die Domain **frei** ist.
3) **Alles** landet in einer CSV (vollständige Ergebnisse) + optional Shortlist ≥ 5.000/Monat.

## Features
- **Live-Ansicht** im Browser (Streamlit): Jede geprüfte Domain erscheint sofort mit Status.
- **Seriöse Geschwindigkeit** (Default: 1 Req/Sek., 1 Worker), damit nichts geblockt wird.
- **Fortsetzen** jederzeit möglich – Ergebnisse werden laufend gespeichert.
- **Zwei Exporte**: `full_results.csv` (alles) und `hits_over_5000.csv` (nur ≥5k).
- **Marken-Schutz**: Flag für potenzielle Markenbegriffe (einfache Blacklist) im Ergebnis.

## Installation
1) Python 3.10+ installieren.
2) Im Ordner dieses Tools:
   ```
   pip install -r requirements.txt
   ```

## Start
```
streamlit run app.py
```
Dann im Browser die CSV hochladen (z. B. deine `domain_candidates_6000.csv`) und auf **Start** klicken.

## Hinweise
- **Keine APIs, keine Kosten.** Es werden öffentliche Webseiten schonend abgefragt.
- Bei Captcha/429 pausiert das Tool automatisch und macht langsamer weiter.
- RDAP (kostenfrei, offizieller WHOIS-Nachfolger) ist **optional** zuschaltbar; Default bleibt „Web ohne API“.

## Ergebnis-CSV (Schema)
- domain, is_registered, whois_source, traffic_monthly_est, traffic_source,
  http_status_traffic_page, notes, category, pattern, note_in, tm_flag

## Haftung & Ethik
- Nur generische Domains nutzen, **keine** Marken/UDRP-Risiken.
- Fair Use beachten (Geschwindigkeit nicht hochdrehen).
