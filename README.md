
# fewo-calserver

Ferienwohnungsverwaltung — Flask-App zur Verwaltung von Buchungen, Gästen,
Rechnungen, Warenwirtschaft und Kalender für einen Ferienwohnungsbetrieb.

Architektur- und Datenbankübersicht: siehe [ARCHITEKTUR.md](ARCHITEKTUR.md)

---

# Änderungshistorie

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

    git clone git@bitbucket.org:ralph_mueller/fewo-calserver.git
    cd fewo-calserver

SSH-URL prüfen:

    git remote -v

## 2. Python-Abhängigkeiten installieren

    pipenv install

`bkormlib` liegt direkt im Projekt. `pythonpacks` (für `rmemaillib`) wird
aus dem Nachbar-Repo `../pythonpacks` installiert (Pipfile-Pfad).

## 3. Node-Module (Bootstrap)

    cd flaskr/static
    npm install
    cd ../..

## 4. .env Datei anlegen

Datei `.env` im Projektverzeichnis anlegen (nicht ins Repo einchecken):

    # development oder production
    ENV=development

    # Datenbankverbindung (Entwicklung)
    DEVELOPMENT_DATABASE=mysql+pymysql://user:password@localhost/testrechnungen

    # Datenbankverbindung (Produktion)
    PRODUCTION_DATABASE=mysql+pymysql://user:password@localhost/fewo

    # Flask Secret Key (langen Zufallsstring verwenden)
    SECRET_KEY=<geheimer-schlüssel>

    # E-Mail-Konfiguration
    EMAIL_ADDRESS=fewo@example.com
    EMAIL_USER=fewo@example.com
    EMAIL_PASSWORD=<passwort>
    EMAIL_HOST=smtp.example.com

    # Empfänger für interne Mails (Team-Benachrichtigungen)
    EMAILS_TEAM=team@example.com
    INFO_EMAIL=info@example.com

**Hinweis Entwicklung:** Im `development`-Modus werden Team-Mails an die
in `EMAILS_TEAM` konfigurierte Adresse umgeleitet. Gäste-E-Mails gehen
aber an die echte Gästeadresse — daher im Testbetrieb nur mit
Testbuchungen auf eigene Namen arbeiten.

## 5. Datenbank einrichten

### MySQL-Benutzer und Datenbank anlegen

    CREATE DATABASE testrechnungen CHARACTER SET utf8mb4;
    CREATE USER 'fewouser'@'localhost' IDENTIFIED BY 'passwort';
    GRANT ALL PRIVILEGES ON testrechnungen.* TO 'fewouser'@'localhost';
    FLUSH PRIVILEGES;

**Hinweis MariaDB:** Falls Authentifizierungsprobleme auftreten:

    ALTER USER 'fewouser'@'localhost'
      IDENTIFIED VIA mysql_native_password USING PASSWORD('passwort');

### Neue Tabellen für Warenwirtschaft erstellen

    CREATE TABLE ware (
        id          INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        bezeichnung VARCHAR(255) NOT NULL,
        preis       DECIMAL(10,2) NOT NULL,
        mwst_satz   INT NOT NULL DEFAULT 19,
        menge_lager INT NOT NULL DEFAULT 0,
        mindestbestand INT NOT NULL DEFAULT 0,
        lieferant   VARCHAR(255),
        active      TINYINT(1) NOT NULL DEFAULT 1
    ) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4;

    CREATE TABLE verkauf (
        id                   INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        buchung_id           INT NOT NULL,
        ware_id              INT NOT NULL,
        menge                INT NOT NULL,
        preis_zum_zeitpunkt  DECIMAL(10,2) NOT NULL,
        mwst_zum_zeitpunkt   INT NOT NULL,
        zeitpunkt            DATETIME NOT NULL
    ) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4;

**Hinweis:** Die App verwendet MyISAM — keine Foreign-Key-Constraints in der DB.
Die referenzielle Integrität wird auf Anwendungsebene sichergestellt.

### Produktionsdaten lokal importieren (optional)

    # Dump auf dem Server erstellen
    mysqldump -u user -p fewo > fewo_dump.sql

    # Lokal importieren
    mysql -u fewouser -p testrechnungen < fewo_dump.sql

    # Danach ware- und verkauf-Tabellen anlegen (s.o., falls nicht im Dump)

## 6. Tests ausführen

    # bkormlib-Tests (ORM gegen SQLite in-memory)
    pipenv run pytest bkormlib/tests/

    # App-Tests (Flask Test Client, kein Datenbankzugriff)
    pipenv run pytest tests/

    # Alle Tests
    pipenv run pytest

## 7. Entwicklungsserver starten

    pipenv run flask run

Alternativ mit uWSGI:

    pipenv run uwsgi --http-socket :5000 --module wsgi:application

---

# Produktivbetrieb (Linux-Server)

## uWSGI-Konfiguration (`flaskr.ini`)

    [uwsgi]
    chdir = /home/rmueller/fewo-calserver
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
    User=rmueller
    WorkingDirectory=/home/rmueller/fewo-calserver
    ExecStart=/home/rmueller/.local/bin/pipenv run uwsgi --ini /home/rmueller/fewo-calserver/flaskr.ini
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
