'''
Created on 13.09.2016

Refactoring ongoing (7.3.2019)

@author: ralph
'''

import sys
import json
import datetime
from flask import Flask, render_template
from flask_cors import CORS

# sys.path.append('../../libs') # to include file fewo_reporting
import bkormlib
bkormlib.envir = 'development'
    
    
app = Flask(__name__, instance_relative_config=True)

from . import home
app.register_blueprint(home.bp)
 
@app.route("/resetinvoice/")
def reset_invoice_new():
    return render_template('reset_invoice_new.html', run_mode=bkormlib.envir) 

CORS(app)
app.secret_key = 'google hupf schmeckt gut'

# import auth
# app.register_blueprint(auth.bp)

from . import besucher
app.register_blueprint(besucher.bp)

from . import buchung
app.register_blueprint(buchung.bp)

from . import rest
app.register_blueprint(rest.bp)

# from . import stats
# app.register_blueprint(stats.bp)

from . import fewocalendar
app.register_blueprint(fewocalendar.bp)

from . import json_routes
app.register_blueprint(json_routes.bp)

if __name__ == "__main__":
    app.run(debug=True, port=5000)