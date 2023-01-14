'''
Created on 11.01.2013
Changed on 05.05.2013, (calculation of arrivals and nights
    include all visitors - old, young etc.)
Changed on 31.08.2016 - using peewee ORM to access objects,
    results were compared with the old reporting function and are
    the same (August 2016)
Changed on 3.10.2018, better reporting for nights / arrival per country
Fixed bug on 3.1.0.2018: departure on first day of month doesn't account
    for any nights in this month

@author: ralph
'''

import datetime
import calendar
from peewee import fn
# from playhouse.shortcuts import model_to_dict
from bkormlib.schema import Buchung, Apartment


# -------------------- functions ------------------

def report_stats_for_month(month, year):

    arrivals_dict = dict()
    arrivals_sum = 0
    nights_sum = 0
    kurtaxe = 0.0
    nights_ueber_15_kt = 0
    nights_ueber_15 = 0
    nights_ueber_10_kt = 0
    nights_unter_10 = 0
    transactions = []
    email_addresses = set()

    visits = (
        Buchung
        .select()
        .where(
            # departure on first day of month doesn't account for any
            # nights in this month (3.10.2018)
            (Buchung.abreise > datetime.date(year, month, 1))
            & (Buchung.abreise <= datetime.date(
                year, month, calendar.monthrange(year, month)[1]))
            & (Buchung.status == 'abgerechnet')
        ))

    for visit in visits:
        # collect unique email addresses
        email_addresses.add(visit.besucher.email)

        # Deal with arrivals first
        arrivals = visit.arrivals_for_month(month, year)
        if arrivals > 0:
            if visit.besucher.land not in arrivals_dict.keys():
                arrivals_dict[visit.besucher.land] = {
                    'arrivals': 0, 'nights': 0}
            arrivals_dict[visit.besucher.land]['arrivals'] += arrivals
            arrivals_sum += arrivals

        # kurtaxe
        kurtaxe += float(visit.kurtaxe)
        #  format of nights_report: [ü15kt, ü15, ü10, u10, country]

        nights_report = visit.nights_report(month, year)

        if visit.besucher.land not in arrivals_dict.keys():
            arrivals_dict[visit.besucher.land] = {'arrivals': 0, 'nights': 0}
        arrivals_dict[visit.besucher.land]['nights'] += nights_report[4]

        nights_sum += nights_report[4]
        nights_ueber_15_kt += nights_report[0]
        nights_ueber_15 += nights_report[1]
        nights_ueber_10_kt += nights_report[2]
        nights_unter_10 += nights_report[3]

    return ({'kurtaxe': kurtaxe,
             'arrivals_sum': arrivals_sum,
             'arrivals': arrivals_dict,
             'nights_sum': nights_sum,
             'kt_nights': nights_ueber_15_kt,
             'nights_ueber_15_kt': nights_ueber_15_kt,
             'nights_ueber_15': nights_ueber_15,
             'nights_ueber_10_kt': nights_ueber_10_kt,
             'nights_unter_10': nights_unter_10,
             'transactions': transactions},
            email_addresses)


def financials_for_month(month, year):

    query = (
        Buchung
        .select(
            fn.SUM(Buchung.miete).alias('miete'),
            fn.SUM(Buchung.kurtaxe).alias('kurtaxe'),
            fn.SUM(Buchung.vorauszahlung).alias('vorauszahlung'),
            fn.SUM(Buchung.vip_passes).alias('vip_paesse'),
            fn.SUM(Buchung.kommission).alias('kommission'),
            Buchung.apartment.alias('id'))
        .where(
            (Buchung.abreise >= datetime.date(year, month, 1))
            & (Buchung.abreise <= datetime.date(
                year, month, calendar.monthrange(year, month)[1]))
            & (Buchung.status == 'abgerechnet')
        )
        .group_by(Buchung.apartment))

    miete = 0
    kurtaxe = 0
    kommission = 0
    vorauszahlungen = 0.0

    fewo_vector = []

    for r in query:
        miete += float(r.miete)
        kurtaxe += float(r.kurtaxe)
        kommission += float(r.kommission)
        vorauszahlungen += float(r.vorauszahlung)
        fewo_vector.append((
            Apartment.get(Apartment.id == r.id).name,
            float(r.miete),
            float(r.kurtaxe), float(r.kommission)))

    pretty_string = (
        "\n\n"
        "Einnahmen:        {0: 8.2f} €\n"
        "Vorauszahlungen:  {1: 8.2f} €\n"
        "Kurtaxe           {2: 8.2f} €\n"
        "Kommission        {3: 8.2f} €\n").format(
            miete,
            vorauszahlungen,
            kurtaxe,
            kommission)
    for v in fewo_vector:
        pretty_string += (
            "\nWohnung {}     Miete:{:8.2f} €    Kommission:{:8.2f} €"
            .format(v[0], v[1], v[3]))
    return ({
        'miete': miete,
        'kurtaxe': kurtaxe,
        'kommission': kommission,
        'vorauszahlungen': vorauszahlungen,
        'fewo_vector': fewo_vector,
        'pretty': pretty_string})


def aggregate_byMonth_byApartment(status='abgerechnet'):
    '''
    Aggregate for bookings for status ('storno' | 'abgerechnet' | 'gebucht')
    select COUNT(id), SUM(miete), YEAR(abreise), MONTH(abreise), apartment_id
        from buchung
        GROUP BY YEAR(abreise), MONTH(abreise), apartment_name
    '''
    query = (
        Buchung
        .select(Buchung.apartment,
                fn.COUNT(Buchung.id).alias('count'),
                fn.SUM(Buchung.miete).alias('miete'),
                fn.YEAR(Buchung.abreise).alias('year'),
                fn.MONTH(Buchung.abreise).alias('month'))
        .where(Buchung.status == status)
        .group_by(
            fn.YEAR(Buchung.abreise),
            fn.MONTH(Buchung.abreise),
            Buchung.apartment)
    )
    return ([{
        'count': x.count,
        'rent': x.miete,
        'year': x.year,
        'month': x.month,
        'Apartment': x.apartment.name} for x in query])


def calc_apartment_income_and_commission_for_years(apartment_name, years):
    apt = Apartment.get(Apartment.name == apartment_name)
    income = []
    commission = []
    for year in years:
        startdate = datetime.date(year, 1, 1)
        enddate = datetime.date(year, 12, 31)
        res = (
            Buchung
            .select(
                fn.sum(Buchung.miete).alias('income'),
                fn.sum(Buchung.kommission).alias('kommission'))
            .where(
                (Buchung.abreise >= startdate)
                & (apt.id == Buchung.apartment_id)
                & (Buchung.abreise <= enddate)
                & (Buchung.status << ['abgerechnet', 'gebucht'])
            )).scalar(as_tuple=True)
        if res[0] is not None:
            income.append(float(res[0]))
            commission.append(float(res[1]))
        else:
            income.append(0.0)
            commission.append(0.0)

    return income, commission


def calc_income_and_commission_for_years(years):
    income = []
    commission = []
    for year in years:
        startdate = datetime.date(year, 1, 1)
        enddate = datetime.date(year, 12, 31)
        res = (
            Buchung
            .select(
                fn.sum(Buchung.miete).alias('income'),
                fn.sum(Buchung.kommission).alias('kommission'))
            .where(
                (Buchung.abreise >= startdate)
                & (Buchung.abreise <= enddate)
                & (Buchung.status << ['abgerechnet', 'gebucht'])
            )).scalar(as_tuple=True)
        if res[0] is not None:
            income.append(float(res[0]))
            commission.append(float(res[1]))
        else:
            income.append(0)
            commission.append(0)
    return income, commission


def calc_income_all_apartments_for_years(apartment_names, years):
    dataset = []
    for apt_name in apartment_names:
        apt = Apartment.get(Apartment.name == apt_name)
        income = []
        for year in years:
            startdate = datetime.date(year, 1, 1)
            enddate = datetime.date(year, 12, 31)
            res = (
                Buchung
                .select(fn.sum(Buchung.miete).alias('income'))
                .where(
                       (Buchung.abreise >= startdate)
                       & (apt.id == Buchung.apartment_id)
                       & (Buchung.abreise <= enddate)
                       & (Buchung.status << ['abgerechnet', 'gebucht'])
                )).scalar(as_tuple=True)
            if res[0] is not None:
                income.append(float(res[0]))
            else:
                income.append(0.0)
        dataset.append(income)
    return dataset


def calc_income_apartment(apt_name, year):
    startdate = datetime.date(year, 1, 1)
    enddate = datetime.date(year, 12, 31)
    apt = Apartment.get(Apartment.name == apt_name)
    bookings = (
        Buchung
        .where(
            (Buchung.abreise >= startdate)
            & (apt.id == Buchung.apartment_id)
            & (Buchung.abreise <= enddate)
            & (Buchung.status << ['abgerechnet', 'gebucht'])
        ))
    miete = 0
    days_for_daily_rate = 0
    for b in bookings:
        # calculate sum rent income
        miete += b.miete
        # calulate average rent / day
        days_for_daily_rate += b.miete/(b.abreise-b.anreise).days
        # calculate days in year
    return [
        float(miete),
        len(bookings),
        float(days_for_daily_rate/len(bookings))]


def calc_forecast_today():

    dataset = []
    years = [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
    for year in years:
        today_in_year = datetime.date(
            year,
            datetime.date.today().month,
            datetime.date.today().day)

        query = (
            Buchung
            .select(
                fn.COUNT(Buchung.id).alias('bookings'),
                fn.SUM(Buchung.miete).alias('miete_sum'),
                fn.SUM(Buchung.kurtaxe).alias('kurtaxe_sum'))
            .where(
                (Buchung.status << ['abgerechnet', 'gebucht']) &
                (fn.YEAR(Buchung.abreise) == year) &
                (Buchung.tscreated <= today_in_year))
        )

        res = query[0]
        dataset.append(
            (year, res.bookings, float(res.miete_sum), float(res.kurtaxe_sum)))

    return dataset


def calc_actuals_today():

    dataset = []
    years = [2017, 2018, 2019, 2020, 2021, 2022, 2023]
    for year in years:
        today_in_year = datetime.date(
            year,
            datetime.date.today().month,
            datetime.date.today().day)

        query = (
            Buchung
            .select(
                fn.COUNT(Buchung.id).alias('bookings'),
                fn.SUM(Buchung.miete).alias('miete_sum'),
                fn.SUM(Buchung.kurtaxe).alias('kurtaxe_sum'))
            .where(
                (Buchung.status << ['abgerechnet']) &
                (fn.YEAR(Buchung.abreise) == year) &
                (Buchung.rechnungsdatum <= today_in_year))
        )

        res = query[0]
        if res.bookings == 0:
            dataset.append((year, 0, 0, 0))
        else:
            dataset.append(
                (
                    year, res.bookings,
                    float(res.miete_sum),
                    float(res.kurtaxe_sum)))
    return dataset


def show_forecast_by_month(year):
    '''
        return the forcast for <year>

    '''

    # year = 2023

    today_in_year = datetime.date(
        year,
        datetime.date.today().month,
        datetime.date.today().day)

    query = (
        Buchung
        .select(
            fn.COUNT(Buchung.id).alias('count'),
            fn.SUM(Buchung.miete).alias('miete'),
            fn.SUM(Buchung.kurtaxe).alias('kurtaxe'),
            fn.MONTH(Buchung.abreise).alias('month'))
        .where(
            (Buchung.status << ['abgerechnet', 'gebucht']) &
            (fn.YEAR(Buchung.abreise) == year) &
            (Buchung.tscreated <= today_in_year)
        )
        .group_by(
            fn.MONTH(Buchung.abreise))
    )
    tupls = [
        (q.month, q.count, float(q.miete), float(q.kurtaxe)) for q in query]
    # fill up tupls to full year (if no bookings for sertain month)
    for month in list(set(range(1, 13, 1)) - set(x[0] for x in tupls)):
        tupls.append((month, 0, 0))
    return tupls


'''
select sum(miete) as 'Miete', sum(kurtaxe) as 'Kurtaxe'
    from buchung
    WHERE
        status in ('abgerechnet', 'gebucht')
        and YEAR(abreise) = 2022
        and tscreated < '2022-01-13'


SELECT COUNT(
    `t1`.`id`) AS `count`,
        SUM(`t1`.`miete`) AS `miete`,
        MONTH(`t1`.`abreise`) AS `month`
    FROM `buchung` AS `t1`
    WHERE ((
        (`t1`.`status` IN ('gebucht'))
        AND EXTRACT(year FROM `t1`.`abreise`)) = 2022)
    GROUP BY MONTH(`t1`.`abreise`);

This works:
SELECT COUNT(
    `t1`.`id`) AS `count`,
    SUM(`t1`.`miete`) AS `miete`,
    SUM(`t1`.`kurtaxe`) AS `kurtaxe`,
    MONTH(`t1`.`abreise`) AS `month`
FROM `buchung` AS `t1`
WHERE
    `t1`.`status` IN ('gebucht', 'abgerechnet')  and
    YEAR (`t1`.`abreise`) = 2022
GROUP BY MONTH(`t1`.`abreise`)
'''
