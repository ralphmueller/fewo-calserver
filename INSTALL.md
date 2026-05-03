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
Kann nach einem Update wiederholt werden, um neue Tabellen nachzuziehen.

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
