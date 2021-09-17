'''
Created on 13.09.2016

Refactoring ongoing (7.3.2019)

@author: ralph
'''

from flask import Flask, render_template
from flask_cors import CORS
from flaskr.auth import login_required
import bkormlib
bkormlib.envir = 'development'
from . import home
from . import auth
from . import besucher
from . import buchung

# sys.path.append('../../libs') # to include file fewo_reporting
import bkormlib
bkormlib.envir = 'development'

app = Flask(__name__, instance_relative_config=True)

CORS(app)
app.secret_key = 'google hupf schmeckt gut'


@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404


app.register_blueprint(home.bp)


@app.route("/resetinvoice/")
@login_required
def reset_invoice_new():
    return render_template('reset_invoice_new.html', run_mode=bkormlib.envir) 


app.register_blueprint(auth.bp)

app.register_blueprint(besucher.bp)

app.register_blueprint(buchung.bp)

from . import rest
app.register_blueprint(rest.bp)

from . import stats
app.register_blueprint(stats.bp)

from . import fewocalendar
app.register_blueprint(fewocalendar.bp)

from . import json_routes
app.register_blueprint(json_routes.bp)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
