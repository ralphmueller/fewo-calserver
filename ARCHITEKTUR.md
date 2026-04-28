# Architektur — fewo-calserver

## App-Architektur

```mermaid
graph TB
    Browser["Browser (Client)"]
    nginx["nginx\n(Reverse Proxy)"]
    uwsgi["uWSGI"]

    subgraph Flask["Flask App (flaskr/)"]
        init["__init__.py\n(App Factory)"]
        blueprints["blueprints.py\n(Blueprint Registration)"]

        subgraph Blueprints["Blueprints"]
            home["home_bp\n/"]
            auth["auth_bp\n/auth"]
            besucher["besucher_bp\n/besucher"]
            buchung["buchung_bp\n/buchung"]
            calendar["calendar_bp\n/calendar"]
            warenwirtschaft["warenwirtschaft_bp\n/warenwirtschaft"]
            stats["stats bp\n/stats"]
            rest["rest bp\n/rest"]
        end

        templates["Templates\n(Jinja2)"]
    end

    subgraph Libs["Bibliotheken"]
        bkormlib["bkormlib/\n(ORM-Modelle, Peewee)"]
        rmemaillib["rmemaillib\n(E-Mail-Versand)"]
    end

    MySQL[("MySQL\n(fewo / testrechnungen)")]
    SMTP["SMTP-Server\n(E-Mail)"]
    pythonpacks["../pythonpacks\n(rmemaillib Quelle)"]

    Browser --> nginx --> uwsgi --> Flask
    Flask --> bkormlib --> MySQL
    Flask --> rmemaillib --> SMTP
    pythonpacks -.->|Pipfile-Pfad| rmemaillib
```

---

## Datenbankschema

```mermaid
erDiagram
    user {
        int id PK
        string username
        string password
        bool admin
    }

    user_logging {
        int id PK
        int user_id FK
        datetime tscreated
        string event_type
    }

    apartment {
        int id PK
        string name
        string beschreibung
        int rechnungs_nummer
        bool active
    }

    preisliste {
        int id PK
        int apartment_id FK
        int year
        float preis_2p
        float preis_2p_long
        float preis_wp
    }

    portalinfo {
        int id PK
        string name
        decimal kommission_prozent
        bool active
        bool collect
    }

    besucher {
        int id PK
        int user_id FK
        string name
        string vorname
        string email
        string anrede
        string land
        string plz
        string stadt
        string strasse
        string tel
        string language
    }

    buchung {
        int id PK
        int user_id FK
        int apartment_id FK
        int besucher_id FK
        int portal_id FK
        date anreise
        date abreise
        string status
        decimal miete
        decimal mwst
        decimal kurtaxe
        decimal summe
        decimal vorauszahlung
        decimal offener_betrag
        decimal kommission
        string rechnungs_nummer
        date rechnungsdatum
    }

    ware {
        int id PK
        string bezeichnung
        decimal preis
        int mwst_satz
        int menge_lager
        int mindestbestand
        string lieferant
        bool active
    }

    verkauf {
        int id PK
        int buchung_id FK
        int ware_id FK
        int menge
        decimal preis_zum_zeitpunkt
        int mwst_zum_zeitpunkt
        datetime zeitpunkt
    }

    email {
        int id PK
        int besucher_id FK
        int buchung_id FK
        string recipient
        string header
        text body
        datetime tscreated
    }

    user ||--o{ user_logging : "hat"
    user ||--o{ besucher : "angelegt von"
    user ||--o{ buchung : "angelegt von"
    apartment ||--o{ buchung : "hat"
    apartment ||--o{ preisliste : "hat"
    besucher ||--o{ buchung : "hat"
    besucher ||--o{ email : "hat"
    portalinfo ||--o{ buchung : "vermittelt"
    buchung ||--o{ verkauf : "enthält"
    buchung ||--o{ email : "hat"
    ware ||--o{ verkauf : "wird verkauft in"
```

---

## Blueprint-Übersicht

| Blueprint | URL-Prefix | Funktion |
|---|---|---|
| `home_bp` | `/` | Startseite, Dashboard |
| `auth_bp` | `/auth` | Login, Logout, Passwort ändern |
| `besucher_bp` | `/besucher` | Gäste-Stammdaten |
| `buchung_bp` | `/buchung` | Buchungen, Rechnungen, Angebote |
| `calendar_bp` | `/calendar` | Kalenderansicht |
| `warenwirtschaft_bp` | `/warenwirtschaft` | Artikelstamm, Lieferungen, Statistik |
| `stats bp` | `/stats` | Umsatzauswertungen |
| `rest bp` | `/rest` | JSON-REST-Endpunkte |
| `json_routes bp` | `/json` | iCal / externe Feeds |
| `info_bp` | `/info` | System-Info |

---

## Verzeichnisstruktur

```
fewo-calserver/
├── bkormlib/               ORM-Modelle (Peewee), Tests
│   ├── schema.py           Alle Datenbankmodelle
│   ├── __init__.py         Exports
│   └── tests/              pytest gegen SQLite in-memory
├── flaskr/                 Flask-App
│   ├── __init__.py         App Factory
│   ├── blueprints.py       Blueprint-Registrierung
│   ├── auth/               Authentifizierung
│   ├── besucher/           Gäste-Verwaltung
│   ├── buchung/            Buchungs-Verwaltung
│   ├── calendar/           Kalender
│   ├── warenwirtschaft/    Warenwirtschaft
│   ├── home/               Startseite
│   ├── static/             CSS, JS (Bootstrap via npm)
│   ├── templates/          Globale Templates (layout, nav, rechnung)
│   └── utils/              Hilfsfunktionen, Fehlerseiten
├── tests/                  App-Tests (Flask Test Client)
├── config.py               Konfigurationsklassen (dev/prod)
├── wsgi.py                 WSGI Entry Point
├── flaskr.ini              uWSGI-Konfiguration
├── Pipfile                 Python-Abhängigkeiten
└── .env                    Secrets (nicht im Repo)
```
