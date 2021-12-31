'''
Created on 31.12.2021

@author: ralph

use flask_assets to minify / uglify css and js assets

'''
from flask import current_app as app
from flask_assets import Environment, Bundle

assets = Environment(app)

bundles = {
    'all_js': Bundle(
        "node_modules/jquery/dist/jquery.js",
        "node_modules/bootstrap/dist/js/bootstrap.js",
        "node_modules/chart.js/dist/chart.js",
        "node_modules/rx/dist/rx.lite.compat.js",
        "js/chart_functions.js",
        "js/lookup_besucher.js",
        "js/buchung.js",
        "js/lookup_besucher.js",
        output='dist/all.js'),
    'all_css': Bundle(
        'node_modules/bootstrap/dist/css/bootstrap.css',
        'css/myapp.css',
        output='dist/all.css',
        filters='cssmin')}

assets.register(bundles)

