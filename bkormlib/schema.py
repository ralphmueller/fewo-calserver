'''
:created: 27.12.2015

:author: ralph_mueller

Minor updates all along the way
'''

import calendar
import os
from datetime import datetime, date, time
from playhouse.db_url import connect
from peewee import (
    BooleanField,
    Model,
    CharField,
    DecimalField,
    IntegerField,
    DateTimeField,
    ForeignKeyField,
    DateField,
    TimeField,
    TextField,
    FloatField,
    BlobField,
    DatabaseProxy
)


database_proxy = DatabaseProxy()


def db_connect(mode, url):
    '''
        connect to database
    '''
    db = connect(url)
    database_proxy.initialize(db)
    return db


class UnknownField(object):
    ''' pass on unknown fields '''


class BaseModel(Model):
    ''' collect common model extensions to peweee model here '''
    class Meta:
        '''
            Good place to store proxy until initialized
        '''
        database = database_proxy


class User(BaseModel):
    '''
        Entails the users of the system,
        admin == True gives access to admin information
    '''
    username = CharField(unique=True, null=False)
    password = CharField(null=False)
    admin = BooleanField(null=False)

    class Meta:
        '''
            DB table name
        '''
        db_table = 'user'


class UserLogging(BaseModel):
    ''' persist user interactions to data base '''
    user = ForeignKeyField(User, backref='user_logging')
    tscreated = DateTimeField(null=True)
    event_type = CharField(null=False)

    class Meta:
        '''
            DB table name
        '''
        db_table = 'user_logging'


class Portal(BaseModel):
    ''' model class for booking portals '''
    name = CharField(null=True)
    kommission_prozent = DecimalField(default=0.0)
    active = BooleanField(null=False)
    collect = BooleanField(null=False)

    @classmethod
    def choices(cls):
        """
            list of portals-id/name pairs
        """
        portals = Portal.select().where(Portal.active)
        return [(portal.id, portal.name) for portal in portals]

    class Meta:
        '''
            DB table name
        '''
        db_table = 'portalinfo'


class Apartment(BaseModel):
    ''' object model for apartments '''
    beschreibung = CharField(null=True)
    lat = FloatField(null=True, default=0)
    lng = FloatField(null=True, default=0)
    name = CharField(null=True)
    rechnungs_nummer = IntegerField(default=0)
    tscreated = DateTimeField(null=True)
    tslastupdate = DateTimeField(null=True)
    feratel_link = CharField(null=True)
    active = BooleanField(null=False)
    active_visits = []

    class Meta:
        '''
            DB table name
        '''
        db_table = 'apartment'

    @classmethod
    def choices(cls):
        """
            list of apartment-id/name pairs
        """
        apts = Apartment.select().where(Apartment.active)
        return [(apt.id, apt.name) for apt in apts]

    def get_next_invoice_no(self):
        '''
        increase current invoice number count for this apartment, save it and
        return it

        :return: invoice number for next invoice
        '''
        self.rechnungs_nummer += 1
        self.save()
        return self.rechnungs_nummer

    def calendar_support(self):
        '''
            set local variable active_visits for active bookings for
            the current and future for a given apartment
        '''
        if self.active_visits == []:
            beginning_of_current_month = date(
                    datetime.now().year,
                    datetime.now().month,
                    1)
            res = (
                Buchung
                .select()
                .where(
                    (Buchung.apartment == self) &
                    ((Buchung.status == 'gebucht') |
                        (Buchung.status == 'abgerechnet')) &
                    ((Buchung.anreise >= beginning_of_current_month) |
                        (Buchung.abreise >= beginning_of_current_month))
                )
                .order_by(Buchung.anreise)
            )
            self.active_visits = [b for b in res]
        return self.active_visits

    def check_availability(self, anreise, abreise):
        """
            Apartment method to check if Apartment is avail for date pair
            This is True if none of the following conditions is True if
            any of the follwoing bookings already exists
            - booking with equal dates
            - boking with anreise in the past and departure in the future
            - booking.anreise after anreise and departure before departure
            - booking.anreise before departure and booking.abreise after
              departure
            - booking.anreise before anreise and booking.abreise after
              anreise
            Bookings have to be for
            - this apartment
            - of status 'gebucht' or 'abgerechnet'

            :return: True if apartment is available for time period
        """
        res = (
            Buchung
            .select()
            .where(
                (
                    (Buchung.apartment_id == self.id) &
                    (Buchung.status << ['gebucht', 'abgerechnet']) &
                    (
                        (
                            (Buchung.anreise < anreise) &
                            (Buchung.abreise > abreise)) |
                        (
                            (Buchung.anreise == anreise) &
                            (Buchung.abreise == abreise)) |
                        (
                            (Buchung.anreise > anreise) &
                            (Buchung.abreise < abreise)) |
                        (
                            (Buchung.anreise < abreise) &
                            (Buchung.abreise > abreise)) |
                        (
                            (Buchung.anreise < anreise) &
                            (Buchung.abreise > anreise))
                    )
                )
            )
        )
        return len(list(res)) == 0

    def get_preisliste_year(self, year):
        '''
            get Preisliste for year
            :param: year
            :return: Preisliste for year
        '''
        return (
            Preisliste
            .get(Preisliste.apartment == self, Preisliste.year == year))

    def get_price_for_stay(self, arrival, departure, tenants=2):
        """
            calculate the total price for a stay excluding kurtaxe
            :params: arrival -> Date
                - depature
                - tenats - number of tenants (2 if ommitted)
            Get Preisliste for year (derived from arrival). Get the righ
            daily rate (less for stays over 5 nights) for the first
            2 tenants and add the per diem for additional tenants
            return:
                - price for stay
        """
        preisliste = self.get_preisliste_year(arrival.year)
        nights = (departure - arrival).days
        if nights < 6:
            day_rate = preisliste.preis_2p
        else:
            day_rate = preisliste.preis_2p_long
        return (
            (day_rate + (tenants - 2) * preisliste.preis_wp) * nights)


class Preisliste(BaseModel):
    '''
        Preisliste Übernachtungen
        - ein Eintrag pro Jahr und Apartment

        - preis_wp: der Preis für jede weitere Person
    '''
    apartment = ForeignKeyField(Apartment, backref='preislisten')
    year = IntegerField(null=False)
    preis_2p = FloatField(null=False)
    preis_2p_long = FloatField(null=False)
    preis_wp = FloatField(null=False, default=7)

    class Meta:
        '''
            DB table name
        '''
        db_table = 'preisliste'


class Besucher(BaseModel):
    '''
        Besucher is a central class of the system. All bookings
        made are related to a besucher. A besucher is created and
        stored with all the data relevant to
        - create bookings
        - list past and future bookings for the besucher
        - provide information to contact besucher
        - provide information like home address etc.
    '''
    user = ForeignKeyField(User, backref='besucher')
    anrede = CharField(null=False, default='Fam')
    email = CharField()
    land = CharField(default='DE')
    name = CharField(null=False)
    vorname = CharField(null=False)
    firmenname = CharField(null=True)
    nobesuche = IntegerField(db_column='noBesuche', null=True)
    plz = CharField(default='')
    stadt = CharField(default='')
    strasse = CharField(default='')
    tel = CharField(default='')
    tscreated = DateTimeField(null=True)
    tslastupdate = DateTimeField(null=True)
    vermerk = CharField(default='')
    lat = FloatField(null=True)
    lng = FloatField(null=True)
    language = CharField(null=False, default='DE')

    class Meta:
        '''
            DB table name
        '''
        db_table = 'besucher'


class Buchung(BaseModel):
    ''' Describes Buchung and provides methods needed  '''
    user = ForeignKeyField(User, backref='buchungen')
    apartment = ForeignKeyField(Apartment, backref='buchungen')
    besucher = ForeignKeyField(Besucher, backref='buchungen')
    portal = ForeignKeyField(Portal)
    ankunftszeit = TimeField(default=time(0, 0))
    abreise = DateField(null=True)
    anreise = DateField(null=True)
    kommission = DecimalField(default=0.0)
    kommission_prozent = DecimalField(default=0.0)
    kurtaxe = DecimalField(default=0.0)
    kurtaxe_korrekturwert = DecimalField(default=0.0)
    kurtaxe_hz = IntegerField(default=0)
    kurtaxe_kinder = IntegerField(default=0)
    kurtaxe_nz = IntegerField(default=0)
    kurtaxe_vz = IntegerField(default=0)
    meldeschein_nummer = CharField(default="")
    miete = DecimalField(default=0.0)
    mwst = DecimalField(default=0.0)
    notiz = CharField(default="")
    offener_betrag = DecimalField(default=0.0)
    preis_nacht = DecimalField(default=0.0)
    rabatt = DecimalField(default=0.0)
    rechnungs_nummer = CharField(default="")
    rechnungsdatum = DateField(null=True)
    status = CharField(default="")
    summe = DecimalField(default=0.0)
    tscreated = DateTimeField(null=True)
    tslastupdate = DateTimeField(null=True)
    vip_passes = IntegerField(default=0)
    vorauszahlung = DecimalField(default=0.0)
    zusatzkosten = DecimalField(default=0.0)

    class Meta:
        '''
            DB table name
        '''
        db_table = 'buchung'

    # getters (convert decimal to float)
    def get_preis_nacht(self):
        ''' :getter: price for one night '''
        return float(self.preis_nacht)

    def get_rabatt(self):
        ''' :getter: rebate (percantage) '''
        return float(self.rabatt)

    def get_vorauszahlung(self):
        ''' :getter: prepayment '''
        return float(self.vorauszahlung)

    def get_zusatzkosten(self):
        ''' :getter: additional cost '''
        return float(self.zusatzkosten)

    def get_kurtaxe_vz(self):
        ''' :getter: kurtaxe full '''
        return int(self.kurtaxe_vz)

    def get_kurtaxe_hz(self):
        ''' :getter: kurtaxe half '''
        return int(self.kurtaxe_hz)

    def get_kurtaxe_kinder(self):
        ''' :getter: kurtaxe kinder (should always be 0) '''
        return int(self.kurtaxe_kinder)

    def get_kurtaxe_nz(self):
        return int(self.kurtaxe_nz)

    def get_summe(self):
        ''' :getter: sum up kurtaxe and rent '''
        return float(self.summe)

    def get_miete(self):
        ''' :getter: rent for the stay '''
        return float(self.miete)

    def get_kurtaxe(self):
        ''' :getter: sum kurtaxe for the stay '''
        return float(self.kurtaxe)

    def get_kurtaxe_korrekturwert(self):
        return float(self.kurtaxe_korrekturwert)

    def get_mwst(self):
        ''' :getter: VAT for stay '''
        return float(self.mwst)

    def get_offener_betrag(self):
        ''' :getter: outstanding payment (summe - prepayment) '''
        return float(self.offener_betrag)

    def get_kommission_prozent(self):
        ''' :getter: commision payment portals '''
        return float(self.kommission_prozent)

    def get_notiz(self):
        ''' :getter: notiz '''
        return self.notiz

    def get_anreise(self):
        ''' :getter: arrival date '''
        return self.anreise

    def get_abreise(self):
        ''' :getter: departure date '''
        return self.abreise

    def get_portal(self):
        ''' :getter: portal '''
        return self.portal

    # calculated

    def get_nights(self):
        ''' :getter: nuber of night for stay '''
        return (self.abreise - self.anreise).days

    def arrivals_for_month(self, month, year):
        '''
            how many people arrived for this booking
            :param: month, year
        '''
        if self.anreise.month != month or self.anreise.year != year:
            return 0
        else:
            return (self.kurtaxe_hz + self.kurtaxe_nz +
                    self.kurtaxe_vz + self.kurtaxe_kinder)

    def recalc(self, status):
        """
            nötige Werte neu berechnen und setzen
            - status: neu
            - miete, kurtaxe, summe, offener_betrag, kommission

            Annahme: die Grundwerte  (preis/nacht, anzahl besucher)
        """

        self.status = status
        self.miete = (
            self.get_preis_nacht() * self.get_nights() *
            (1.0 - self.get_rabatt()/100.0) +
            self.get_zusatzkosten()
        )

        self.mwst = round(
            self.miete - self.miete /
            (1 + StaticValuesBuchung.mwstsatz()/100), 2
        )

        self.kurtaxe = (
            (
                self.get_kurtaxe_vz() * StaticValuesBuchung.ktsatz_vz() +
                self.get_kurtaxe_hz() * StaticValuesBuchung.ktsatz_hz()
            ) * self.get_nights() - self.get_kurtaxe_korrekturwert()
        )

        self.summe = self.get_kurtaxe() + self.get_miete()

        self.offener_betrag = self.get_summe() - self.get_vorauszahlung()

        self.kommission_prozent = self.portal.kommission_prozent
        self.kommission = (
            self.get_miete() *
            self.get_kommission_prozent()
            / 100)
        return self

    def save(self, *args, **kwargs):
        ''' update time stamp last visit and save '''
        self.tslastupdate = datetime.now()
        return super(Buchung, self).save(*args, **kwargs)

    def happened(self):
        """
        did visit happen?
        """
        return (self.status == 'abgerechnet')

    def cancelled(self):
        '''
            :return: True if booking was cancelled
        '''
        return (not self.happened())

    def nights_for_month(self, month, year, visitors):
        '''
            nights stayed for a given month
            ex: arr Jan 27, leave Feb 3 then nights in Jan include
                the night Feb 1, so nights in Jan are 4, nights in Feb are 2
            multiply with number of adults (over 15) visiting
            visitors are the type of people visiting ... ü15, ü15_kt,
                ü_10, kinder
        '''
        start_of_month = date(year, month, 1)
        end_of_month = date(
                year,
                month,
                calendar.monthrange(year, month)[1]
            )
        # arrival is after month or departure is before month
        if (self.abreise <= start_of_month or end_of_month < self.anreise):
            return 0

        # arrival and departure in same month
        if self.anreise.month == month and self.abreise.month == month:
            return (self.abreise - self.anreise).days * visitors

        if self.anreise.month == month:
            # arr date is in month
            return (
                (calendar.monthrange(year, month)[1] - self.anreise.day)
                * visitors)
        else:
            # departure date is in month
            return (self.abreise.day) * visitors

    def nights_per_month_ueber_15_kt(self, month, year):
        return self.nights_for_month(month, year, self.kurtaxe_vz)

    def nights_per_month_ueber_15(self, month, year):
        return self.nights_for_month(month, year, self.kurtaxe_nz)

    def nights_per_month_ueber_10_kt(self, month, year):
        return self.nights_for_month(month, year, self.kurtaxe_hz)

    def nights_per_month_unter_10(self, month, year):
        return self.nights_for_month(month, year, self.kurtaxe_kinder)

    def nights_report(self, month, year):
        #
        # combine nights report in one array
        #
        return ([self.nights_per_month_ueber_15_kt(month, year),
                 self.nights_per_month_ueber_15(month, year),
                 self.nights_per_month_ueber_10_kt(month, year),
                 self.nights_per_month_unter_10(month, year),
                 self.nights_per_month_ueber_15_kt(month, year) +
                self.nights_per_month_ueber_15(month, year) +
                self.nights_per_month_ueber_10_kt(month, year) +
                self.nights_per_month_unter_10(month, year),
                 self.besucher.land])

    def __str__(self):
        return '{0:<15s} ( \
                {1} Personen KT, \
                {2} Personen ohne KT, \
                {3} KT Kinder) {4} {5} - {6} {7:2} Nächte, \
                Preis € {8} Kurtaxe € {9} Portal {10} Kommission {11} \n' \
            .format(self.besucher.name,     # 0
                    self.kurtaxe_vz,        # 1
                    self.kurtaxe_nz,        # 2
                    self.kurtaxe_hz,        # 3
                    self.apartment.name,    # 4
                    self.anreise,           # 5
                    self.abreise,           # 6
                    str((self.abreise - self.anreise).days),    # 7
                    str(self.miete),        # 8
                    str(self.kurtaxe),      # 9
                    self.portal.name,       # 10
                    self.kommission)        # 11


    def get_waren_summe(self):
        """Gesamtbetrag aller verkauften Waren für diese Buchung."""
        return sum(
            float(v.preis_zum_zeitpunkt) * v.menge
            for v in self.verkaeufe
        )

    def get_waren_mwst(self):
        """MwSt.-Aufschlüsselung der Waren: {satz: betrag_brutto}."""
        result = {}
        for v in self.verkaeufe:
            satz = v.mwst_zum_zeitpunkt
            brutto = float(v.preis_zum_zeitpunkt) * v.menge
            result[satz] = result.get(satz, 0.0) + brutto
        return result


class Ware(BaseModel):
    """Artikelstamm für den Warenverkauf an Gäste."""
    bezeichnung = CharField()
    preis = DecimalField(decimal_places=2)
    mwst_satz = IntegerField(default=19)
    menge_lager = IntegerField(default=0)
    mindestbestand = IntegerField(default=0)
    lieferant = CharField(null=True)
    active = BooleanField(default=True)

    class Meta:
        db_table = 'ware'

    @classmethod
    def choices(cls):
        waren = Ware.select().where(Ware.active).order_by(Ware.bezeichnung)
        return [(w.id, w.bezeichnung) for w in waren]


class Verkauf(BaseModel):
    """Einzelner Warenverkauf — verknüpft eine Buchung mit einer Ware."""
    buchung = ForeignKeyField(Buchung, backref='verkaeufe')
    ware = ForeignKeyField(Ware, backref='verkaeufe')
    menge = IntegerField()
    preis_zum_zeitpunkt = DecimalField(decimal_places=2)
    mwst_zum_zeitpunkt = IntegerField()
    zeitpunkt = DateTimeField(default=datetime.now)

    class Meta:
        db_table = 'verkauf'


class Email(BaseModel):
    ''' model class for emails '''
    besucher = ForeignKeyField(Besucher, backref='emails')
    buchung = ForeignKeyField(Buchung, backref='emails')
    body = TextField()
    header = CharField()
    recipient = CharField()
    tscreated = DateTimeField(null=True)

    class Meta:
        db_table = 'email'



class StaticValuesBuchung():
    @classmethod
    def ktsatz_vz(cls):
        return float(os.environ.get('KURTAXE_SATZ_VZ', '2.1'))

    @classmethod
    def ktsatz_hz(cls):
        return float(os.environ.get('KURTAXE_SATZ_HZ', '0.5'))

    @classmethod
    def mwstsatz(cls):
        return int(os.environ.get('MWST_SATZ', '7'))

    @classmethod
    def today(cls):
        return date.today()


class Migration(BaseModel):
    description = CharField()
    migration = CharField()
    timestamp = DateTimeField()

    class Meta:
        db_table = 'migration'


