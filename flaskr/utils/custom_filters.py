'''
Created on 29.12.2021

@author: ralph

collect all custom filters in a file outside of __init__.py

'''
import re
from babel.numbers import format_decimal, format_percent
from babel.numbers import format_currency
from babel.dates import format_date
from flask import current_app as app


@app.template_filter()
def rabatt(value):
    return '{} %'.format(value)


@app.template_filter()
def euro_percent(value):
    return format_percent(value, locale='de_DE')


@app.template_filter()
def euro_decimal(value):
    return format_decimal(value, locale='de_DE')


@app.template_filter()
def euro_currency(value):
    return format_currency(value, '€', locale='de_DE')


@app.template_filter()
def euro_date(value):
    return format_date(value, locale='de_DE', format="full")


@app.template_filter()
def euro_date_short(value):
    return format_date(value, locale='de_DE', format="short")


@app.template_filter()
def en_date(value):
    return format_date(value, locale='en')


@app.template_filter()
def filter_db_url(db_url):
    return re.sub(r":\w+@", ":_______@", db_url)
