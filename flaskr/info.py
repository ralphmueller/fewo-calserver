'''
Created on 28.12.2021

@author: ralph
'''
from datetime import datetime
from flask import Blueprint, render_template, current_app
from flaskr.utils.api import SystemInfo
import config

info_bp = Blueprint(
    'info_bp',
    __name__,
    url_prefix='/info',
    template_folder='templates',
    static_folder='static'
)


@info_bp.route('/')
def info():
    return render_template(
        'info.html',
        dt=datetime.now(),
        title='Info',
        sysinfo=SystemInfo,
        no_besucher=SystemInfo.get_number_of_visitors(),
        no_buchungen=SystemInfo.get_number_of_bookings(),
        config=config.Config,
        run_mode=current_app.env)
