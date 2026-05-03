"""
Flask CLI commands for database setup and administration.

Usage:
    pipenv run flask --app flaskr init-db
    pipenv run flask --app flaskr create-admin --username admin --password geheim
"""

import click
from flask import current_app
from werkzeug.security import generate_password_hash


def register_commands(app):
    app.cli.add_command(init_db)
    app.cli.add_command(create_admin)


@click.command('init-db')
def init_db():
    """Create all database tables (safe — never drops existing data)."""
    from bkormlib.schema import (
        User, UserLogging, Portal, Apartment, Preisliste,
        Besucher, Buchung, Email, Migration,
        Ware, Verkauf,
    )
    db = current_app.config['DB']
    models = [
        User, UserLogging, Portal, Apartment, Preisliste,
        Besucher, Buchung, Email, Migration,
        Ware, Verkauf,
    ]
    db.create_tables(models, safe=True)
    click.echo(f'Tabellen angelegt (oder bereits vorhanden): {len(models)} Modelle.')


@click.command('create-admin')
@click.option('--username', prompt=True, help='Benutzername')
@click.option('--password', prompt=True, hide_input=True,
              confirmation_prompt=True, help='Passwort')
@click.option('--admin', is_flag=True, default=True,
              help='Admin-Rechte vergeben (Standard: ja)')
def create_admin(username, password, admin):
    """Create a new user (admin by default)."""
    from bkormlib.schema import User
    if User.select().where(User.username == username).exists():
        click.echo(f'Fehler: Benutzer "{username}" existiert bereits.', err=True)
        raise SystemExit(1)
    User.create(
        username=username,
        password=generate_password_hash(password),
        admin=admin,
    )
    role = 'Admin' if admin else 'Benutzer'
    click.echo(f'{role} "{username}" wurde angelegt.')
