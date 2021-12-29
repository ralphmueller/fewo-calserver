'''
Created on 29.12.2021

@author: ralph

collect all blueprints in a file outside of __init__.py

'''

from flask import current_app as app

from .home import home
from .auth import auth
from .besucher import besucher
from .buchung import buchung
from . import rest
from . import stats
from .calendar import calendar
from . import json_routes
from . import info

app.register_blueprint(home.home_bp)
app.register_blueprint(auth.auth_bp)
app.register_blueprint(besucher.besucher_bp)
app.register_blueprint(buchung.buchung_bp)
app.register_blueprint(rest.bp)
app.register_blueprint(stats.bp)
app.register_blueprint(calendar.calendar_bp)
app.register_blueprint(json_routes.bp)
app.register_blueprint(info.info_bp)
