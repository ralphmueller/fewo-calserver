
# fewo-calserver

Ferienwohnungsverwaltung — Flask-App zur Verwaltung von Buchungen, Gästen,
Rechnungen, Warenwirtschaft und Kalender für einen Ferienwohnungsbetrieb.

Architektur- und Datenbankübersicht: siehe [ARCHITEKTUR.md](ARCHITEKTUR.md)

---

# Änderungshistorie

## Rev: 1.9 (02.05.2026)

### Open-Source-Vorbereitung

Alle betreiberspezifischen Werte aus dem Code entfernt und in `.env` ausgelagert:
Firmenname, Adresse, IBAN, Telefon, E-Mail, WLAN-SSID, Kurtaxe-Sätze,
Stornobedingungen, Feratel Accommodation-ID und Apartment-Mapping.

Neuer Jinja2-Context-Processor stellt `operator.*`-Variablen in allen Templates bereit.
`StaticValuesBuchung` liest Kurtaxe- und MwSt-Sätze jetzt aus env vars (mit Defaults).

**Neue Dateien:**
- `LICENSE` — MIT License
- `.env.example` — vollständige Dokumentation aller `.env`-Variablen mit Platzhaltern

---

## Rev: 1.8 (02.05.2026)

### HTMX-Modernisierung: Zweistufiger Buchungsflow und Warenverkauf inline

Die Buchungsoberfläche wurde vollständig auf HTMX umgestellt —
kein jQuery/RxJS mehr für Interaktionen, alle Seitenaktualisierungen
per HTMX-Partial-Rendering.

**Zweistufiger Buchungsflow** (Neue Buchung, Schnellbuchung, Angebot umwandeln):

- Schritt 1: Buchungsdaten erfassen → **Weiter →**
- Schritt 2: Zusammenfassung (Apartment, Daten, Miete, Kurtaxe, Summe, Offener Betrag) +
  WYSIWYG-E-Mail-Editor (CKEditor) → **Speichern & Senden →**
- **← Zurück** kehrt zu Schritt 1 zurück ohne Datenverlust

**Neue Buchung aus Besucher-Detailkarte:**
Buchungs- und Angebotsformular öffnet sich direkt unterhalb der Besucherkarte,
kein Seitenwechsel.

**Angebot umwandeln:**
Direkt auf der Buchungsdetailseite inline — E-Mail-Editor erscheint auf der Seite,
kein eigener Seitenwechsel mehr.

**Besucherkarte — Buchungshistorie:**
Stornierte und verworfene Buchungen werden ausgeblendet.
Nur `angebot`, `gebucht` und `abgerechnet` sind sichtbar.

**FlaskrSession entfernt:**
Die DB-persistierte Session-Tabelle (`flaskrsession`) wird nicht mehr befüllt.
Die Tabelle in der DB bleibt erhalten, das Modell und alle Routen wurden entfernt.

**Warenverkauf inline:**
Abgerechnete Buchungen zeigen jetzt direkt in der Buchungsdetailansicht
eine „Warenverkauf"-Karte — Artikel auswählen, Menge eingeben, Lager wird
sofort aktualisiert, kein Seitenwechsel. Validierungsfehler erscheinen inline.

**CKEditor** wird global über `/static/node_modules/ckeditor4/ckeditor.js`
eingebunden. **HTMX 2.0.4** wird per CDN (unpkg.com) geladen.

---

## Rev: 1.7 (29.04.2026)

### Feratel Gästemeldung automatisiert

Neues Modul `flaskr/feratel/` zur automatischen Übermittlung von
Gästemeldungen an das Feratel Deskline WebClient4-System per Browser-Automation
(Playwright / Chromium).

**Funktionsumfang:**

- Button „An Feratel melden" direkt in der Buchungsansicht (abgerechnete Buchungen)
- Playwright steuert einen headless Chromium-Browser:
  - Login mit Credentials aus `.env`
  - Apartment-Auswahl anhand des Buchungs-Apartments
  - Neuen Meldeschein öffnen
  - Anreise- und Abreisedatum setzen
  - Hauptgast suchen (im Feratel-Adresssystem) oder manuell eintragen
  - Weitere Gäste hinzufügen wenn `kurtaxe_vz > 1`
  - Meldeschein speichern, Nummer auslesen
- Vergebene Meldeschein-Nummer wird in `buchung.meldeschein_nummer` gespeichert
- Wiederholtes Melden möglich (Button wechselt auf „Erneut melden")

**Mock-Modus:**

Für Entwicklung und Tests kann die echte Feratel-Verbindung durch einen Mock
ersetzt werden — kein Browser wird gestartet:

    # in .env
    FERATEL_MOCK=true

Im Mock-Modus wird eine gefälschte Meldeschein-Nummer (`MOCK-YYYYMMDDHHMMSS`)
zurückgegeben und der komplette Vorgang nur geloggt.

**Neue `.env`-Variablen:**

    FERATEL_ID=<Feratel-Benutzername>
    FERATEL_PW=<Feratel-Passwort>
    FERATEL_MOCK=true   # true = Mock, false/weggelassen = echter Browser

**Neue Abhängigkeiten:**

    pipenv install playwright
    pipenv run playwright install chromium

---

## Rev: 1.6 (28.04.2026)

### Warenwirtschaft

Neues Modul zur Verwaltung von Waren und Warenverkauf an Gäste.

- Artikelstamm: Bezeichnung, Preis, MwSt.-Satz (7 % / 19 %), Lieferant, Aktiv-Flag
- Lagerbestandsverwaltung mit Mindestbestand und Ampel-Anzeige
- Lieferungen: Zugänge werden auf den aktuellen Bestand addiert
- Warenverkauf direkt aus der Buchungsansicht (laufendes Tab)
- Automatische Lagerbestandsreduktion beim Verkauf; Storno stellt Bestand wieder her
- Preis- und MwSt.-Snapshot zum Verkaufszeitpunkt
- Warenblock auf der Endrechnung (separater MwSt.-Ausweis)
- Statistik: Top-Artikel, Erlös nach Jahr/Monat, Lagerbestand-Ampel

Neue DB-Tabellen: `ware`, `verkauf`

Detaillierte Beschreibung: [Erweiterung Warenwirtschaft.md](Erweiterung%20Warenwirtschfaft.md)

## Rev: 1.5 (28.04.2026)

### bkormlib ins Projekt integriert

`bkormlib` wird nicht mehr als Teil von `pythonpacks` ausgeliefert, sondern
liegt jetzt direkt im Projektverzeichnis unter `bkormlib/`. Änderungen am
ORM-Schema werden hier vorgenommen.

`pythonpacks` (Repo `../pythonpacks`) wird weiterhin für `rmemaillib`
verwendet und im Pipfile als Pfad-Abhängigkeit referenziert.

### Tests eingeführt

Zwei unabhängige Test-Suites:

**App-Tests** (`tests/`) — Flask-Routen, Auth, REST-API, Kalender-Logik.
Laufen mit gemocktem `bkormlib`, kein Datenbankzugriff nötig.

    pipenv run pytest tests/

**bkormlib-Tests** (`bkormlib/tests/`) — ORM-Modelle gegen SQLite in-memory.
Testen Buchungslogik, Kurtaxe-Berechnung, Verfügbarkeitsprüfung, Preisliste.

    pipenv run pytest bkormlib/tests/

Alle Tests zusammen:

    pipenv run pytest

### Bugfix: Besucherliste bei leerem Ergebnis

`fetch_visitors()` gab `None` zurück wenn keine Besucher vorhanden waren,
was zu einem Redirect auf die Startseite führte. Die Funktion gibt jetzt
immer eine Liste zurück (ggf. leer).

---

## Rev: 1.4 (04.09.2023)

Fixed calendar FiG Website links (Prices)

## Rev: 1.2 (28.02.2023)

### Liste Rechnungen und Buchungen

* getrennt nach Monaten anzeigbar
* Liste Rechnungen: alle Rechnungen mit Abreise im gewählten Monat, sortiert nach absteigendem Datum
* Liste Buchungen: alle Rechnungen mit Anreise im gewählten Monat, sortiert nach aufsteigendem Datum

### FLASK_ENV

was deprecated in the current FLASK release, so I took it out. .env file still reads ENV variable to configure the DB, mailer, etc.

### Logging

added simple code to flaskr/__init__.py to supress url logging on console

## Rev: 1.1

Kurtaxe ändert sich für 2023

[Beschluss Stadt Gersfeld](https://www.gersfeld.de/satzungen-gebuehren.html)

Kurze Zusammenfassung der Änderungen ab 2023:

* Kurbeitrag nach Vollendung des 14. Lebensjahres: 2,10€
* Für Ausübung des Berufes: 0,50€
* bis Vollendung des 14. Lebensjahres: 0,00€
* verschiedene Ausnahmen

---

# Installation

## Voraussetzungen

- Python >= 3.9
- pipenv (`pip install pipenv`)
- Node.js / npm (für Bootstrap)
- MySQL >= 5.7 oder MariaDB >= 10.3
- Repo `../pythonpacks` ausgecheckt (für `rmemaillib`)

## 1. Repository klonen

    git clone https://github.com/USERNAME/fewo-calserver.git
    cd fewo-calserver

## 2. Python-Abhängigkeiten installieren

    pipenv install

`bkormlib` liegt direkt im Projekt. `pythonpacks` (für `rmemaillib`) wird
aus dem Nachbar-Repo `../pythonpacks` installiert (Pipfile-Pfad).

## 3. Node-Module (Bootstrap)

    cd flaskr/static
    npm install
    cd ../..

## 4. .env Datei anlegen

    cp .env.example .env

Anschließend `.env` mit den eigenen Werten befüllen. Die Datei enthält
alle verfügbaren Variablen mit Kommentaren. Pflichtfelder:

| Variable | Beschreibung |
|---|---|
| `ENV` | `development` oder `production` |
| `DEVELOPMENT_DATABASE` / `PRODUCTION_DATABASE` | MySQL-Verbindungsstring |
| `SECRET_KEY` | Langer Zufallsstring für Flask-Sessions |
| `EMAIL_*` | SMTP-Zugangsdaten |
| `OPERATOR_NAME` … `OPERATOR_IBAN` | Betreiber-Stammdaten für Rechnungen und E-Mails |
| `KURTAXE_SATZ_VZ`, `KURTAXE_SATZ_HZ`, `MWST_SATZ` | Lokale Abgabensätze |
| `FERATEL_ID`, `FERATEL_PW` | Feratel-Zugangsdaten (nur wenn Feratel genutzt wird) |
| `FERATEL_ACCOMMODATION_ID` | UUID der Unterkunft im Feratel-System |
| `FERATEL_APARTMENT_MAP` | JSON: Apartment-Code → Feratel-Einheitenname |

**Entwicklung ohne Feratel:** `FERATEL_MOCK=true` setzen — kein Browser wird gestartet.

**Hinweis:** Gäste-E-Mails gehen immer an die echte Gästeadresse.
Im Testbetrieb nur mit Buchungen auf eigene Namen arbeiten.

## 5. Datenbank einrichten

### MySQL-Benutzer und Datenbank anlegen

    CREATE DATABASE fewo CHARACTER SET utf8mb4;
    CREATE USER 'fewouser'@'localhost' IDENTIFIED BY 'passwort';
    GRANT ALL PRIVILEGES ON fewo.* TO 'fewouser'@'localhost';
    FLUSH PRIVILEGES;

**Hinweis MariaDB:** Falls Authentifizierungsprobleme auftreten:

    ALTER USER 'fewouser'@'localhost'
      IDENTIFIED VIA mysql_native_password USING PASSWORD('passwort');

### Tabellen anlegen

    pipenv run flask --app flaskr init-db

Legt alle Tabellen an (`safe=True` — bestehende Daten bleiben erhalten).
Bei einer Neuinstallation können so auch neue Tabellen nach einem Update
ohne Datenverlust nachgezogen werden.

### Ersten Admin anlegen

    pipenv run flask --app flaskr create-admin --username admin

Das Passwort wird interaktiv abgefragt (zweimal zur Bestätigung).
Für einen normalen Benutzer ohne Admin-Rechte: `--no-admin`.

### Produktionsdaten lokal importieren (optional)

    # Dump auf dem Server erstellen
    mysqldump -u user -p fewo > fewo_dump.sql

    # Lokal importieren
    mysql -u fewouser -p fewo < fewo_dump.sql

    # Anschließend fehlende Tabellen nachrüsten (idempotent):
    pipenv run flask --app flaskr init-db

## 6. Playwright installieren (nur wenn Feratel-Automation genutzt wird)

    pipenv install playwright
    pipenv run playwright install chromium

Ohne Playwright kann die App normal genutzt werden — der Feratel-Button
ist dann deaktiviert. `FERATEL_MOCK=true` in `.env` umgeht Playwright vollständig.

## 7. Tests ausführen

    # bkormlib-Tests (ORM gegen SQLite in-memory)
    pipenv run pytest bkormlib/tests/

    # App-Tests (Flask Test Client, kein Datenbankzugriff)
    pipenv run pytest tests/

    # Alle Tests
    pipenv run pytest

## 8. Entwicklungsserver starten

    pipenv run flask run

Alternativ mit uWSGI:

    pipenv run uwsgi --http-socket :5000 --module wsgi:application

---

# Produktivbetrieb (Linux-Server)

## uWSGI-Konfiguration (`flaskr.ini`)

    [uwsgi]
    chdir = /home/BENUTZER/fewo-calserver
    module = wsgi
    callable = application

    master = true
    processes = 5

    # Wichtig: verhindert MySQL "out of sync"-Fehler
    lazy = true
    lazy-apps = true

    socket = /tmp/flaskr.sock
    chmod-socket = 666
    vacuum = true

    ignore-sigpipe = true
    ignore-write-errors = true
    disable-write-exception = true

    log-5xx = true
    disable-logging = true

## nginx-Konfiguration

    server {
        listen 80;
        server_name example.com;

        location / {
            include uwsgi_params;
            uwsgi_pass unix:/tmp/flaskr.sock;
        }
    }

## Systemd-Service (`/etc/systemd/system/flaskr.service`)

    [Unit]
    Description=uWSGI fewo-calserver
    After=syslog.target

    [Service]
    User=BENUTZER
    WorkingDirectory=/home/BENUTZER/fewo-calserver
    ExecStart=/home/BENUTZER/.local/bin/pipenv run uwsgi --ini /home/BENUTZER/fewo-calserver/flaskr.ini
    Restart=always
    KillSignal=SIGQUIT
    Type=idle
    StandardError=syslog
    NotifyAccess=all

    [Install]
    WantedBy=multi-user.target

Starten und beim Boot aktivieren:

    sudo systemctl start flaskr.service
    sudo systemctl enable flaskr.service

---

# Bedienungsnotizen

## Besucher-Suche

`*` sind Wildcard-Zeichen

| Eingabe | Ergebnis |
|---|---|
| `Müller` | alle mit Nachnamen Müller |
| `*Müller` | Namen die auf Müller enden (Eide-Müller, Buchmüller) |
| `Müller*` | Namen die mit Müller beginnen (Müller-Waldheim) |
| `*Müller*` | Namen die Müller enthalten |

## Warenwirtschaft

- **Artikelstamm** — Waren anlegen und Stammdaten pflegen (Preis, MwSt, Lieferant, Aktiv)
- **Lieferung** — Zugang zur Ware buchen; wird auf aktuellen Bestand addiert
- **Verkauf** — aus der Buchungsdetailansicht: Artikel und Menge wählen, Lager wird automatisch reduziert
- **Storno** — einzelne Verkäufe können storniert werden; Lager wird wiederhergestellt
- **Statistik** — Top-Artikel nach Umsatz, Erlös nach Jahr/Monat, Lagerbestand-Ampel
