# Bill of Materials — fewo-calserver

Alle Laufzeit-Abhängigkeiten mit Versionsinformation und Lizenz.
Stand: Mai 2026

---

## Backend — Python-Pakete

| Paket | Version | Lizenz | Zweck |
|---|---|---|---|
| Flask | 2.3.1 | BSD-3-Clause | Web-Framework |
| Peewee | 4.0.5 | MIT | ORM (MySQL, SQLite) |
| PyMySQL | 1.1.2 | MIT | MySQL-Treiber |
| Flask-WTF | 1.3.0 | BSD-3-Clause | Formularverarbeitung, CSRF-Schutz |
| WTForms | 3.2.1 | BSD-3-Clause | Formular-Definitionen und Validierung |
| Babel | 2.18.0 | BSD-3-Clause | Internationalisierung, Datumsformatierung |
| python-dotenv | 1.2.2 | BSD-3-Clause | `.env`-Datei laden |
| Flask-Assets | 2.1.0 | BSD-2-Clause | CSS/JS-Asset-Bundles |
| webassets | 3.0.0 | BSD-2-Clause | Asset-Pipeline (cssmin, jsmin) |
| flask-cors | 6.0.2 | MIT | CORS-Header |
| email-validator | 2.3.0 | MIT | E-Mail-Adress-Validierung |
| blinker | 1.9.0 | MIT | Flask-Signale |
| uWSGI | aktuell | GPL-2.0 | WSGI-Server (Produktion) |
| Playwright | 1.59.0 | Apache-2.0 | Browser-Automation (Feratel) |
| pytest-playwright | 0.7.2 | Apache-2.0 | Playwright-Pytest-Plugin |

### Eigene Bibliotheken

| Paket | Lizenz | Zweck |
|---|---|---|
| `bkormlib` (im Repo) | privat | ORM-Modelle (Peewee-Schema) |
| `rmemaillib` (../pythonpacks) | privat | E-Mail-Versand (SMTP) |

---

## Frontend — npm-Pakete (flaskr/static/node_modules/)

| Paket | Version | Lizenz | Zweck |
|---|---|---|---|
| Bootstrap | 5.1.0 | MIT | CSS-Framework, Responsive Grid |
| jQuery | 3.6.0 | MIT | DOM-Hilfsbibliothek, Datepicker |
| CKEditor 4 | 4.16.2 | GPL-2.0+ / LGPL-2.1+ / MPL-1.1 | WYSIWYG-Editor für E-Mail-Texte |
| Chart.js | 3.5.1 | MIT | Diagramme in der Statistik |
| bootstrap-datepicker | 1.9.0 | Apache-2.0 | Datumsauswahl-Widget |

> **Hinweis CKEditor 4:** CKEditor 4 steht unter einer Dreifachlizenz
> (GPL 2.0+, LGPL 2.1+, MPL 1.1). Für den privaten/internen Betrieb
> ist keine gesonderte Lizenz erforderlich. Ab CKEditor 4.22 gilt
> ausschließlich die GPL-2.0+ (Open-Source-Lizenz). Die hier verwendete
> Version 4.16.2 fällt noch unter die Dreifachlizenz.

---

## Frontend — CDN-Einbindungen (layout.html)

| Bibliothek | Version | Lizenz | Einbindung |
|---|---|---|---|
| HTMX | 2.0.4 | Zero-Clause BSD (0BSD) | `https://unpkg.com/htmx.org@2.0.4` |

> **Hinweis HTMX:** Die Zero-Clause BSD Lizenz erlaubt uneingeschränkte
> Nutzung ohne Namensnennung. HTMX kann alternativ lokal aus npm
> eingebunden werden (`npm install htmx.org`).

---

## Entwicklungs-Tools (nicht in der Produktion)

| Tool | Lizenz | Zweck |
|---|---|---|
| pytest | MIT | Test-Framework |
| flake8 | MIT | Linting |
| autopep8 | MIT | Code-Formatierung |
| flask-debugtoolbar | BSD-3-Clause | Debug-Toolbar im Browser |
| Chromium (via Playwright) | BSD | Headless-Browser für Feratel-Automation |

---

## Laufzeitumgebung

| Komponente | Lizenz | Hinweis |
|---|---|---|
| Python ≥ 3.9 | PSF License | |
| MySQL ≥ 5.7 / MariaDB ≥ 10.3 | GPL-2.0 | Datenbankserver |
| nginx | BSD-2-Clause | Reverse Proxy (Produktion) |
| Node.js / npm | MIT | Nur Build-Zeit (npm install) |
