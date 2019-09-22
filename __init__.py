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

sys.path.append('../libs') # to include file fewo_reporting

import bkormlib
bkormlib.envir = 'test'
    
if __name__ == "__main__":
    
    app = Flask(__name__)

    @app.route("/")
    def home():
        return render_template('index.html', title="Willkommen", run_mode=bkormlib.envir)
     
    @app.route("/resetinvoice/")
    def reset_invoice_new():
        return render_template('reset_invoice_new.html', run_mode=bkormlib.envir)
    
    CORS(app)
    app.secret_key = 'google hupf schmeckt gut'
    
    import besucher
    app.register_blueprint(besucher.bp)

    import buchung
    app.register_blueprint(buchung.bp)
    
    import rest
    app.register_blueprint(rest.bp)
    
    import stats
    app.register_blueprint(stats.bp)
    
    import fewocalendar
    app.register_blueprint(fewocalendar.bp)
    
    import json_routes
    app.register_blueprint(json_routes.bp)
    
    app.run(debug=True, port=5000)