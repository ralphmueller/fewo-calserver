'''
Created on 13.09.2016

Refactoring ongoing (7.3.2019)

@author: ralph
'''

import datetime
from flask import Flask, render_template, current_app
from flask_cors import CORS
from flaskr.auth import login_required
import bkormlib
bkormlib.envir = 'development'


# sys.path.append('../../libs') # to include file fewo_reporting

app = Flask(__name__, instance_relative_config=False)

app.config.from_object('config.Config')

CORS(app)

app_context = app.app_context()
app_context.push()

with app.app_context():
    from . import home
    from . import auth
    from .besucher import routes as besucher
    from . import buchung
    from . import rest
    from . import stats
    from . import fewocalendar
    from . import json_routes

    app.register_blueprint(home.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(besucher.besucher_bp)
    app.register_blueprint(buchung.bp)
    app.register_blueprint(rest.bp)
    app.register_blueprint(stats.bp)
    app.register_blueprint(fewocalendar.bp)
    app.register_blueprint(json_routes.bp)

    @app.errorhandler(404)
    def page_not_found(e):
        # note that we set the 404 status explicitly
        return render_template('404.html'), 404


    @app.errorhandler(500)
    def internal_error(e):
        # note that we set the 500 status explicitly
        return render_template('500.html'), 500


    @app.route("/resetinvoice/")
    @login_required
    def reset_invoice_new():
        return render_template('reset_invoice_new.html', run_mode=bkormlib.envir)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
