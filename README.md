
# Latest

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
immer eine Liste zurück (ggf. leer). Das Template zeigt in diesem Fall
„Keine Besucher gefunden".

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

Anpassung der App zum 1. Januar 2023 

Einige kleine Änderungen / Verbesserungen

# Installation

## Voraussetzungen

- Python >= 3.9
- pipenv
- Node.js / npm
- MySQL-Datenbank
- `../pythonpacks` Repo ausgecheckt (für `rmemaillib`)

## Repository klonen

    git clone git@bitbucket.org:ralph_mueller/fewo-calserver.git

SSH-URL setzen:

    git remote set-url origin git@bitbucket.org:ralph_mueller/fewo-calserver.git
    git remote -v

## Node modules

    cd flaskr/static
    npm install

## pipenv

    pipenv install

`bkormlib` liegt direkt im Projekt. `pythonpacks` (für `rmemaillib`) wird
aus dem Nachbar-Repo `../pythonpacks` installiert.

## .env Datei

Enthält Datenbankverbindung, Secret Key und E-Mail-Konfiguration.
Vorlage (Werte anpassen):

    ENV=development
    DEVELOPMENT_DATABASE=mysql+pymysql://user:password@localhost/fewo
    SECRET_KEY=<geheimer-schlüssel>
    EMAIL_ADDRESS=...
    EMAIL_USER=...
    EMAIL_PASSWORD=...
    EMAIL_HOST=...

## Tests ausführen

    # App-Tests (kein Datenbankzugriff nötig)
    pipenv run pytest tests/

    # bkormlib-Tests (SQLite in-memory)
    pipenv run pytest bkormlib/tests/

    # Alle Tests
    pipenv run pytest

## Testlauf (Entwicklung)

    pipenv run uwsgi --http-socket :5000 --module wsgi:application

## uwsgi conf (flaskr.ini)

Important: To avoid error like [mysql out of sync](https://github.com/PyMySQL/PyMySQL/issues/563) see link (https://stackoverflow.com/questions/22752521/uwsgi-flask-sqlalchemy-and-postgres-ssl-error-decryption-failed-or-bad-reco) use the fix below.

	[uwsgi]

	# important: change target directory to actual settings
	chdir = /home/pi/fewo-calserver

	module = wsgi
	callable = application

	master = true
	processes = 5

	# the fix
	lazy = true
	lazy-apps = true

	socket = /tmp/flaskr.sock
	chmod-socket = 666
	vacuum = true

	# os writer error

	ignore-sigpipe = true
	ignore-write-errors = true
	disable-write-exception = true

	# logging

	log-5xx = true
	disable-logging = true

## nginx conf

    server {
        listen 80;
        server_name server_domain_or_IP;

        location / {
            include uwsgi_params;
            uwsgi_pass unix:/tmp/flaskr.sock;
        }
    }

## Run as service /etc/systemd/system/fewo-calserver.service

    location: /etc/systemd/system/flaskr.service

start: 

	sudo systemctl start flaskr.service

load on startup: 

	sudo systemctl enable flaskr.service

Type=idle    - waits for everything else being started .. [link](https://superuser.com/questions/544399/how-do-you-make-a-systemd-service-as-the-last-service-on-boot/573761#573761)

Source

    [Unit]
    Description=uWSGI fewo-calserver
    After=syslog.target

    [Service]
    User=<user>
    WorkingDirectory=/home/<dir>/fewo-calserver

    # Linux Server Gersfeld
    ExecStart=/home/rmueller/.local/bin/pipenv run uwsgi --ini /home/rmueller/fewo-calserver/flaskr.ini

    # Requires systemd version 211 or newer
    Restart=always
    KillSignal=SIGQUIT
    Type=idle
    StandardError=syslog
    NotifyAccess=all

    [Install]
    WantedBy=multi-user.target

# Bedienungsnotizen

## Besucher Suche

`*` sind Wildcard-Zeichen

| Eingabe | Ergebnis |
|---|---|
| `Müller` | alle mit Nachnamen Müller |
| `*Müller` | Namen die auf Müller enden (Eide-Müller, Buchmüller) |
| `Müller*` | Namen die mit Müller beginnen (Müller-Waldheim) |
| `*Müller*` | Namen die Müller enthalten |
