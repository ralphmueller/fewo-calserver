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

> Dokumentation folgt — wird mit dem HTMX-Umbau ergänzt.

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
