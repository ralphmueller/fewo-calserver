# fewo-calserver

Webbasierte Verwaltungssoftware für kleine Ferienwohnungsbetriebe.
Entwickelt für einen Betrieb mit mehreren Wohnungen — einsetzbar für jeden
ähnlichen Betrieb durch Konfiguration über `.env`.

**Tech-Stack:** Python · Flask · Peewee ORM · MySQL/MariaDB · HTMX · Bootstrap 5

---

## Was die App kann

- **Buchungen** — anlegen, bearbeiten, zweistufiger Buchungsflow mit E-Mail-Bestätigung
- **Gäste** — Stammdaten, Buchungshistorie, Schnellsuche mit Wildcards
- **Rechnungen** — druckfertige Rechnung mit MwSt.-Ausweis und Kurtaxe-Abrechnung
- **Warenwirtschaft** — Artikelstamm, Lagerbestand, Verkauf aus der Buchungsansicht
- **Statistik & Forecast** — Einnahmen, Nächte, Kurtaxe nach Monat/Jahr/Wohnung
- **Feratel-Meldung** — automatische Gästemeldung per Browser-Automation (Playwright) ⚠️ Proof of Concept, noch nicht produktionsreif
- **Kalender** — Monatsübersicht aller Belegungen

Alle betreiberspezifischen Werte (Name, Adresse, IBAN, Kurtaxe-Sätze, Feratel-Zugänge)
werden über `.env` konfiguriert — kein Hardcoding im Code.

---

## Schnellstart

    git clone https://github.com/USERNAME/fewo-calserver.git
    cd fewo-calserver
    pipenv install
    cp .env.example .env          # .env mit eigenen Werten befüllen
    pipenv run flask --app flaskr init-db
    pipenv run flask --app flaskr create-admin --username admin
    pipenv run flask run

Die App ist danach erreichbar unter `http://127.0.0.1:5000`.

---

## Dokumentation

| Dokument | Inhalt |
|---|---|
| [INSTALL.md](INSTALL.md) | Vollständige Installationsanleitung (Python, Node, DB, uWSGI, nginx, systemd) |
| [HANDBUCH.md](HANDBUCH.md) | Bedienungsanleitung für den laufenden Betrieb |
| [ARCHITEKTUR.md](ARCHITEKTUR.md) | Architektur- und Datenbankübersicht, Modulstruktur |
| [CHANGELOG.md](CHANGELOG.md) | Änderungshistorie aller Versionen |
| [BILL_OF_MATERIALS.md](BILL_OF_MATERIALS.md) | Alle verwendeten Bibliotheken und Lizenzen |
| [LICENSE](LICENSE) | MIT License |
| [.env.example](.env.example) | Alle konfigurierbaren Variablen mit Kommentaren |
