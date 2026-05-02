# FewoApp — Benutzerhandbuch

Verwaltungsoberfläche für Ferienwohnungen Gersfeld/Rhön.
Lokal erreichbar unter `http://127.0.0.1:5001`, Produktion unter der konfigurierten Server-URL.

---

## Login / Logout

- Einstieg über `/auth/login` mit Benutzername und Passwort
- Session bleibt aktiv bis zum Logout oder Browser-Schließen
- Passwort ändern: Menü → **Admin → Passwort ändern**

---

## Besucher

### Suchen

Menü → **Besucher → Suchen**

Das Suchfeld reagiert automatisch nach 300 ms Tippverzögerung — kein Enter nötig.
Mindestens 3 Zeichen eingeben.

| Eingabe | Ergebnis |
|---|---|
| `Müller` | exakt |
| `Müll*` | beginnt mit „Müll" |
| `*müller` | endet auf „müller" |
| `*müller*` | enthält „müller" |
| `Müll* Ral*` | Nachname beginnt mit „Müll" **und** Vorname mit „Ral" |

### Detailansicht

Klick auf eine Zeile in der Ergebnisliste öffnet direkt darunter eine Detailkarte mit:

- Kontaktdaten (Adresse, E-Mail, Telefon, Vermerk)
- Buchungshistorie (letzte 8 aktive Buchungen, klickbar) — Storni und Verworfene werden ausgeblendet
- Aktions-Buttons: **Bearbeiten**, **Neue Buchung**, **Neues Angebot**

Kein Seitenwechsel — die Suche bleibt aktiv.

### Neue Buchung / Neues Angebot aus der Detailkarte

Über **Neue Buchung** oder **Neues Angebot** in der Besucher-Detailkarte öffnet sich
ein zweistufiges Formular direkt unterhalb der Karte:

**Schritt 1 — Buchungsdaten:**
Anreise, Abreise, Apartment, Portal, Preis/Nacht, Kurtaxe-Personen, Vorauszahlung,
Zusatzkosten, Rabatt, Notiz eingeben → **Weiter →**

**Schritt 2 — E-Mail bearbeiten:**
- Zusammenfassung (Apartment, Daten, Nächte, Miete, Kurtaxe, Summe, Offener Betrag)
- Vorausgefüllter E-Mail-Text im WYSIWYG-Editor — individuell anpassbar
- **Speichern & Senden →** — Buchung wird gespeichert, E-Mail an den Gast verschickt
- **← Zurück** — zurück zu Schritt 1

### Besucher bearbeiten

In der Detailkarte auf **Bearbeiten** klicken.
Das Bearbeitungsformular öffnet sich im selben Panel.

- **Speichern** → aktualisierte Detailkarte erscheint sofort
- **Abbrechen** → zurück zur Detailkarte ohne Änderungen

### Neuen Besucher anlegen

Menü → **Besucher → Neu** oder Button „+ Besucher" in der Navigation.
Nach dem Anlegen wird direkt zur Detailseite weitergeleitet.

---

## Buchungen

Menü → **Buchungen**

### Buchungsliste

Die Liste zeigt alle Buchungen des gewählten Monats.

**Filter — alle ohne Seitenwechsel:**

| Filter | Bedienung |
|---|---|
| Jahr | Klick auf Jahreszahl |
| Monat | Klick auf Monatsname |
| Status | Checkboxen: Gebucht / Abgerechnet / Angebot |
| Wohnung | Dropdown „Alle Wohnungen" oder einzelne Wohnung |
| Gast | Freitextsuche mit Wildcard (`Müll*`, `Müll* Ral*`) |

### Detailansicht

Klick auf eine Zeile klappt die Details **direkt darunter** auf:

- Anreise, Abreise, Nächte, Apartment, Portal
- Miete, Kurtaxe, Summe, Vorauszahlung, Restbetrag (rot wenn > 0)
- Kurtaxe-Belegung (Personen ab 14J / Beruflich / Kinder / Befreit)
- Notiz, Meldeschein-Nr., Rechnungsnummer (wenn vorhanden)

Nochmals klicken schließt die Detailzeile.

### Schnell-Statuswechsel

In der **Status-Spalte** der Liste: Dropdown direkt in der Zeile.

| Von | Nach |
|---|---|
| Angebot | Gebucht oder Verworfen |
| Gebucht | Storno |

> Für „Gebucht → Abgerechnet" den Button **Abrechnen** im Detailpanel nutzen
> (erfordert Meldeschein-Nummer und generiert Rechnungsnummer).

### Buchung bearbeiten

Im Detailpanel → **Bearbeiten**. Das Formular öffnet sich inline.

- Alle Felder editierbar (Datum, Apartment, Portal, Preise, Kurtaxe, Notiz)
- **Speichern** → Detailkarte aktualisiert sich, Update-E-Mail wird verschickt
- **Abbrechen** → zurück zur Detailkarte

### Neue Buchung

Menü → **Buchungen → Neue Buchung** (`/buchung/neu`)

1. Name eintippen (ab 3 Zeichen) → Gästeliste erscheint
2. Gast anklicken → Buchungsformular (Schritt 1) lädt
3. Felder ausfüllen → **Weiter →**
4. E-Mail im WYSIWYG-Editor prüfen / anpassen → **Speichern & Senden →**

### Schnellbuchung

Menü → **Buchungen → Schnellbuchung** (`/buchung/schnell`)

Optimiert für Telefonanfragen:

1. **Anreise + Abreise** eingeben → **Verfügbare Wohnungen prüfen**
2. Freie Wohnung auswählen
3. Gast suchen (ab 2 Zeichen) **oder** „+ Neuen Gast anlegen" (Miniformular)
4. Buchungsformular: Preis/Nacht (aus Preisliste vorausgefüllt), Portal, Personen, Vorauszahlung
5. **Angebot erstellen** oder **Direkt buchen** → E-Mail-Editor öffnet sich (Schritt 2)
6. E-Mail prüfen / anpassen → **Speichern & Senden →**

### Buchung anzeigen

Klick auf eine Buchungszeile in der Liste oder auf eine Buchung in der Besucherkarte
öffnet die Buchungsdetailseite (`/buchung/anzeigen/<id>`).

Je nach Status stehen folgende Aktionen zur Verfügung:

| Status | Aktionen |
|---|---|
| Angebot | **Bearbeiten**, **Umwandeln in Buchung**, **Verwerfen** |
| Gebucht | **Bearbeiten**, **Abrechnen**, **Storno** |
| Abgerechnet | **Feratel melden** |

**Angebot umwandeln:**
Klick auf **Umwandeln in Buchung** öffnet direkt auf der Seite den E-Mail-Editor
mit vorausgefülltem Bestätigungstext. Nach **Bestätigung senden & Buchung speichern →**
wird der Status auf „gebucht" gesetzt und die E-Mail verschickt.
Mit **Abbrechen** wird das Panel wieder geschlossen.

---

## Warenwirtschaft

Menü → **Waren**

### Artikelstamm

Artikel anlegen und Stammdaten pflegen: Bezeichnung, Preis, MwSt.-Satz (7 % / 19 %),
Lieferant, Mindestbestand, Aktiv-Flag.

Lagerbestand-Ampel:
- Grün: Bestand ≥ Mindestbestand
- Gelb: Bestand < Mindestbestand
- Rot: Bestand = 0

### Lieferung buchen

Menü → **Waren → Lieferung**. Zugang wird auf den aktuellen Bestand addiert.

### Verkauf

Aus der Buchungsdetailansicht (Tab „Waren"): Artikel und Menge wählen.
Lager wird automatisch reduziert. Storno stellt Bestand wieder her.

### Statistik

Menü → **Waren → Statistik**

- Top-Artikel nach Umsatz
- Erlös nach Jahr / Monat
- Lagerbestand-Übersicht mit Ampel

---

## Feratel Gästemeldung

In der Buchungsdetailansicht (Status „abgerechnet") erscheint der Abschnitt
**Feratel Meldeschein**.

- **An Feratel melden** — öffnet automatisch den Feratel WebClient4 im Hintergrund
  (headless Chromium), füllt den Meldeschein aus und speichert die vergebene Nummer.
- Nach erfolgreicher Meldung wird die Meldeschein-Nummer in der Buchung angezeigt.
- Erneute Meldung möglich über **Erneut melden**.

> Entwicklung/Test: In `.env` `FERATEL_MOCK=true` setzen — es wird kein
> echter Browser gestartet, die Meldung wird nur geloggt.

---

## Kalender

Menü → **Kalender**

Monatsansicht aller Apartments. Belegungen farblich nach Status:
- gebucht, abgerechnet, Angebot, storniert

---

## Suchwildcard-Referenz

Gilt für alle Suchfelder in der App:

| Zeichen | Bedeutung |
|---|---|
| `*` | beliebig viele Zeichen |
| (kein `*`) | Präfix-Suche: `Müller` findet alles was mit „müller" beginnt |
