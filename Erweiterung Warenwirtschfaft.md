# Erweiterung Warenwirtschaft — Dokumentation

Erstellt: 28.04.2026

---

## Ausgangssituation und Ziel

Im Ferienwohnungsbetrieb sollen Getränke und ähnliche Waren während des
Aufenthalts an Gäste verkauft und auf der Abschlussrechnung abgerechnet werden.

**Anforderungen:**
- Artikelstamm mit Bezeichnung, Preis, MwSt.-Satz, Lager, Lieferant
- Verkauf direkt aus der Buchungsdetailansicht (laufendes Tab)
- Automatische Lagerbestandsreduktion beim Verkauf
- MwSt. pro Artikel: 7 % oder 19 %
- Waren erscheinen additiv auf der bestehenden Endrechnung
- Übernachtungspreise bleiben unverändert (7 % MwSt.); Waren separat ausgewiesen
- Lieferungen als Zugang buchen (addiert auf Bestand)
- Mindestbestand mit Ampel-Warnung

---

## Umgesetzte Funktionen

### 1. Datenbankmodelle (`bkormlib/schema.py`)

Zwei neue Modelle, beide mit `ENGINE=MyISAM` (kein FK-Constraint in DB):

**`Ware`** — Artikelstamm:

| Feld | Typ | Beschreibung |
|---|---|---|
| `bezeichnung` | CharField | Artikelname |
| `preis` | DecimalField(2) | Verkaufspreis brutto |
| `mwst_satz` | IntegerField | 7 oder 19 |
| `menge_lager` | IntegerField | aktueller Lagerbestand |
| `mindestbestand` | IntegerField | Meldegrenze für Ampel |
| `lieferant` | CharField(null) | optional |
| `active` | BooleanField | Artikel aktiv/inaktiv |

**`Verkauf`** — einzelner Warenverkauf (Snapshot-Prinzip):

| Feld | Typ | Beschreibung |
|---|---|---|
| `buchung` | FK → Buchung | zugehörige Buchung |
| `ware` | FK → Ware | verkaufter Artikel |
| `menge` | IntegerField | Stückzahl |
| `preis_zum_zeitpunkt` | DecimalField(2) | Preis zum Kaufzeitpunkt |
| `mwst_zum_zeitpunkt` | IntegerField | MwSt.-Satz zum Kaufzeitpunkt |
| `zeitpunkt` | DateTimeField | Timestamp des Verkaufs |

**Wichtig:** Preis und MwSt. werden als Snapshot gespeichert — spätere
Preisänderungen an der Ware ändern vergangene Verkäufe nicht.

Neue Methoden in `Buchung`:
- `get_waren_summe()` → Gesamtbetrag aller Waren (float)
- `get_waren_mwst()` → dict `{satz: betrag_brutto}` für MwSt.-Aufschlüsselung

### 2. SQL für neue Tabellen

    CREATE TABLE ware (
        id             INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        bezeichnung    VARCHAR(255) NOT NULL,
        preis          DECIMAL(10,2) NOT NULL,
        mwst_satz      INT NOT NULL DEFAULT 19,
        menge_lager    INT NOT NULL DEFAULT 0,
        mindestbestand INT NOT NULL DEFAULT 0,
        lieferant      VARCHAR(255),
        active         TINYINT(1) NOT NULL DEFAULT 1
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

### 3. Blueprint `warenwirtschaft_bp` (`flaskr/warenwirtschaft/`)

| Methode | URL | Funktion |
|---|---|---|
| GET | `/warenwirtschaft/` | Artikelstamm — Liste aller Waren |
| GET/POST | `/warenwirtschaft/create` | Neue Ware anlegen |
| GET/POST | `/warenwirtschaft/update/<id>` | Stammdaten bearbeiten |
| GET/POST | `/warenwirtschaft/lager/<id>` | Lieferung buchen (Zugang addieren) |
| GET | `/warenwirtschaft/statistik` | Statistikseite |
| POST | `/warenwirtschaft/verkauf/<buchung_id>` | Artikel an Buchung verkaufen |
| POST | `/warenwirtschaft/verkauf/delete/<verkauf_id>` | Verkauf stornieren |

### 4. Trennung Stammdaten / Lager

Die Warenverwaltung ist bewusst aufgeteilt:

- **Stammdaten** (`/update`): Bezeichnung, Preis, MwSt., Mindestbestand,
  Lieferant, Aktiv-Flag — für die Pflege der Artikelkonfiguration
- **Lieferung** (`/lager`): Nur Zugang eingeben — der eingegebene Wert wird
  auf den aktuellen Bestand addiert (kein absolutes Überschreiben)

### 5. Lagerbestand-Ampel

In der Statistik und Übersicht werden Artikel nach Lagerstand bewertet:

| Farbe | Bedingung |
|---|---|
| Rot | `menge_lager <= 0` und `mindestbestand > 0` |
| Gelb | `0 < menge_lager <= mindestbestand` |
| Grün | `menge_lager > mindestbestand` oder kein Mindestbestand gesetzt |

### 6. Verkauf aus Buchungsdetailansicht

Im Buchungs-Update-Formular (`/buchung/update/<id>`) gibt es einen neuen
Abschnitt unten:

- Tabelle aller bisheriger Verkäufe dieser Buchung mit Storno-Button
- Formular: Artikel aus Dropdown (nur aktive Waren), Menge eingeben,
  "Hinzufügen"-Button
- Beim Verkauf: Lager wird sofort reduziert; Storno stellt Lager wieder her
- Validierung: Menge > 0; Lager muss ausreichen

### 7. Rechnung (`flaskr/templates/print/rechnung.html`)

Die bestehende `recalc()`-Logik für Übernachtungen bleibt unverändert.
Waren werden additiv ausgewiesen:

- Tabelle der verkauften Artikel (Anzahl × Bezeichnung @ Preis = Betrag)
- MwSt.-Zeile pro Steuersatz (z.B. 19 % auf Waren)
- "Summe Waren"
- "Gesamtsumme" = Übernachtung + Waren
- "Offener Betrag" berücksichtigt Waren

Der Warenblock erscheint nur wenn Verkäufe vorhanden sind.

### 8. Statistik (`/warenwirtschaft/statistik`)

Drei Auswertungen auf einer Seite:

**Top-Artikel** — Verkäufe aggregiert nach Ware:
- Stück verkauft gesamt
- Umsatz brutto gesamt
- Sortiert nach Umsatz absteigend

**Warenerlös nach Jahr und Monat** — Matrix-Tabelle:
- Eine Tabelle pro Jahr
- Spalten: Jan–Dez + Jahressumme
- Leere Monate als `—`

**Lagerbestand** — Ampel-Tabelle:
- Farbiger Punkt (rot/gelb/grün) je nach Bestand vs. Mindestbestand
- Direktlink zur Lieferungs-Seite
- Aktueller Bestand und Mindestbestand nebeneinander

### 9. Navigation

Neuer Dropdown-Eintrag "Waren" in `nav.html` (zwischen Kalender und Statistik):
- Artikelstamm
- Neuer Artikel
- Statistik

### 10. Tests (`bkormlib/tests/test_warenwirtschaft.py`)

10 ORM-Tests gegen SQLite in-memory:
- Ware anlegen (Bezeichnung, Preis, MwSt.-Satz)
- `Ware.choices()` liefert nur aktive Artikel
- MwSt. 7 % korrekt gespeichert
- Lager wird beim Verkauf reduziert
- Storno stellt Lager wieder her
- Preis-Snapshot: Verkauf speichert Preis zum Zeitpunkt, nicht aktuellen Preis
- Backref `buchung.verkaeufe` funktioniert
- `get_waren_summe()` berechnet korrekt
- `get_waren_mwst()` liefert korrekte Aufschlüsselung nach MwSt.-Satz
- `get_waren_summe()` = 0 wenn keine Verkäufe

---

## Offene Punkte

- App-Tests für Warenwirtschaft-Routen (Flask Test Client) noch nicht geschrieben
- REST-Endpunkt `/rest/waren` (aktive Waren als JSON) noch nicht implementiert
- Warenerlös in bestehende Umsatzauswertung (`/stats`) noch nicht integriert
- Tabellen `ware` und `verkauf` müssen auf dem Produktionsserver noch angelegt werden
