'''
Created on 29.12.2021

@author: ralph

collect all blueprints in a file outside of __init__.py

'''
from flask import request, render_template
from flask import current_app as app
from flaskr.api import SystemInfo


def internal_error(e):
    # note that we set the 500 status explicitly
    return render_template('500.html'), 500


def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template(
        '404.html',
        path=request.path,
        base_url=request.base_url,
        version=SystemInfo.version_tag,
        title='Fehler 404 - Seite nicht gefunden',
        run_mode=app.env)


app.register_error_handler(404, page_not_found)
app.register_error_handler(500, internal_error)
