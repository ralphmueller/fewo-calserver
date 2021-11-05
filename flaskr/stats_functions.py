'''
Created on 29.03.2018

@author: ralph

stats functions that prepare data for charts

'''

from peewee import fn
from bkormlib.schema import Buchung, Apartment
import datetime


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

        income.append(float(res[0]))
        commission.append(float(res[1]))
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
        income.append(float(res[0]))
        commission.append(float(res[1]))
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
        .select()
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
