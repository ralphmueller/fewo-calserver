'''
Created on 29.12.2021

@author: ralph

collect all blueprints in a file outside of __init__.py

'''

from flask import current_app as app

from flaskr.home import home
from flaskr.auth import auth
from flaskr.besucher import besucher
from flaskr.buchung import buchung
from flaskr import rest
from flaskr import stats
from flaskr.calendar import calendar
from flaskr import json_routes
from flaskr import info

app.register_blueprint(home.home_bp)
app.register_blueprint(auth.auth_bp)
app.register_blueprint(besucher.besucher_bp)
app.register_blueprint(buchung.buchung_bp)
app.register_blueprint(rest.bp)
app.register_blueprint(stats.bp)
app.register_blueprint(calendar.calendar_bp)
app.register_blueprint(json_routes.bp)
app.register_blueprint(info.info_bp)
