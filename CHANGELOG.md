# Changelog

## Rev 1.9 (02.05.2026)

### Open-Source-Vorbereitung

Alle betreiberspezifischen Werte aus dem Code entfernt und in `.env` ausgelagert:
Firmenname, Adresse, IBAN, Telefon, E-Mail, WLAN-SSID, Kurtaxe-Sätze,
Stornobedingungen, Feratel Accommodation-ID und Apartment-Mapping.

Neuer Jinja2-Context-Processor stellt `operator.*`-Variablen in allen Templates bereit.
`StaticValuesBuchung` liest Kurtaxe- und MwSt-Sätze jetzt aus env vars (mit Defaults).

**Neue Dateien:**
- `LICENSE` — MIT License
- `.env.example` — vollständige Dokumentation aller `.env`-Variablen mit Platzhaltern
- `flaskr/cli.py` — `flask init-db` und `flask create-admin`

---

## Rev 1.8 (02.05.2026)

### HTMX-Modernisierung: Zweistufiger Buchungsflow und Warenverkauf inline

Die Buchungsoberfläche wurde vollständig auf HTMX umgestellt —
kein jQuery/RxJS mehr für Interaktionen, alle Seitenaktualisierungen
per HTMX-Partial-Rendering.

**Zweistufiger Buchungsflow** (Neue Buchung, Schnellbuchung, Angebot umwandeln):
- Schritt 1: Buchungsdaten erfassen → **Weiter →**
- Schritt 2: Zusammenfassung + WYSIWYG-E-Mail-Editor (CKEditor) → **Speichern & Senden →**
- **← Zurück** kehrt zu Schritt 1 zurück ohne Datenverlust

**Weitere Änderungen:**
- Neue Buchung aus Besucher-Detailkarte ohne Seitenwechsel
- Angebot umwandeln inline auf der Buchungsdetailseite
- Stornierte/verworfene Buchungen in der Besucherhistorie ausgeblendet
- FlaskrSession-Tabelle und -Routen entfernt
- Warenverkauf inline in der Buchungsdetailansicht (abgerechnete Buchungen)

---

## Rev 1.7 (29.04.2026)

### Feratel Gästemeldung automatisiert

Neues Modul `flaskr/feratel/` zur automatischen Übermittlung von
Gästemeldungen an das Feratel Deskline WebClient4-System per Browser-Automation
(Playwright / Chromium).

- Button „An Feratel melden" in der Buchungsansicht
- Playwright: Login, Apartment-Auswahl, Meldeschein ausfüllen und speichern
- Meldeschein-Nummer wird in `buchung.meldeschein_nummer` gespeichert
- Mock-Modus: `FERATEL_MOCK=true` — kein Browser, nur Logging

---

## Rev 1.6 (28.04.2026)

### Warenwirtschaft

Neues Modul zur Verwaltung von Waren und Warenverkauf an Gäste.

- Artikelstamm, Lagerbestand mit Mindestbestand und Ampel-Anzeige
- Lieferungen, Verkauf aus der Buchungsansicht, Storno
- Preis- und MwSt.-Snapshot zum Verkaufszeitpunkt
- Warenblock auf der Endrechnung, separater MwSt.-Ausweis
- Statistik: Top-Artikel, Erlös nach Jahr/Monat

Neue DB-Tabellen: `ware`, `verkauf`

---

## Rev 1.5 (28.04.2026)

### bkormlib ins Projekt integriert, Tests eingeführt

- `bkormlib` liegt jetzt direkt im Projektverzeichnis (nicht mehr in `pythonpacks`)
- App-Tests (`tests/`) — Flask-Routen, Auth, REST-API, Kalender
- bkormlib-Tests (`bkormlib/tests/`) — ORM gegen SQLite in-memory
- Bugfix: `fetch_visitors()` gab `None` zurück bei leerem Ergebnis

---

## Rev 1.4 (04.09.2023)

Fixed calendar FiG Website links (Prices)

---

## Rev 1.2 (28.02.2023)

- Buchungs- und Rechnungsliste getrennt nach Monaten
- `FLASK_ENV` entfernt (deprecated)
- Logging-Konfiguration vereinfacht

---

## Rev 1.1

Kurtaxe-Sätze für 2023 angepasst (Vollzahler 2,10 €, Berufstätige 0,50 €).
