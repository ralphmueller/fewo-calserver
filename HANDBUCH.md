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
- Buchungshistorie (letzte 8 Buchungen, klickbar)
- Aktions-Buttons: **Bearbeiten**, **Neue Buchung**, **Neues Angebot**

Kein Seitenwechsel — die Suche bleibt aktiv.

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
2. Gast anklicken → Buchungsformular lädt rechts
3. Felder ausfüllen → **Buchung speichern & E-Mail senden**

Bestätigungs-E-Mail wird automatisch an den Gast verschickt.

### Schnellbuchung

Menü → **Buchungen → Schnellbuchung** (`/buchung/schnell`)

Optimiert für Telefonanfragen:

1. **Anreise + Abreise** eingeben → **Verfügbare Wohnungen prüfen**
2. Freie Wohnung auswählen
3. Gast suchen (ab 2 Zeichen) **oder** „+ Neuen Gast anlegen" (Miniformular)
4. Buchungsformular: Preis/Nacht (aus Preisliste vorausgefüllt), Portal, Personen, Vorauszahlung
5. **Angebot erstellen** oder **Direkt buchen** → E-Mail wird automatisch verschickt

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
