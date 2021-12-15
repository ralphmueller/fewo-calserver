uwsgi --http-socket :5000  --module wsgi:app  --virtualenv /Users/ralph/.local/share/virtualenvs/fewo-calserver-dnC1dOzX

# Installation

## uwsgi conf (flaskr.ini)

    [uwsgi]
    module = wsgi

    master = true
    processes = 5

    socket = /tmp/flaskr.sock
    chmod-socket = 660
    vacuum = true

## nginx conf

server {
    listen 80;
    server_name server_domain_or_IP;

    location / {
        include uwsgi_params;
        uwsgi_pass unix:/tmp/flaskr.sock;
    }
}

## /etc/systemd/system/fewo-calserver.service

[Unit]
Description=uWSGI fewo-calserver
After=syslog.target

[Service]
User=pi
WorkingDirectory=/home/pi/fewo-calserver
ExecStart=/home/pi/.local/bin/pipenv run uwsgi --ini /home/pi/fewo-calserver/flaskr.ini
# Requires systemd version 211 or newer
Restart=always
KillSignal=SIGQUIT
Type=notify
StandardError=syslog
NotifyAccess=all

[Install]
WantedBy=multi-user.target

## get fewo-calendar code

### from bitbucket.org

    git clone https://ralph_mueller@bitbucket.org/ralph_mueller/fewo-calserver.git

## pipenv

## pythonpacks

## node_modules

## .env file

## test run

    pipenv run uwsgi --http-socket :5000  --module wsgi:app

## Besucher Suche

*** sind wildcard Zeichen

Müller - findet alle mit Nachnamen Müller
*Müller - findet alle, deren Namen auf Müller endet (Eide-Müller, Buchmüller)
Müller* - findet alle, deren Namen mit Müller beginnt (Müller-Waldheim, Müller - Testbenutzer)
*Müller* - findet alle, in deren Namen das Wort Müller vorkommt (von Müller-Meier, Müller, Müller-Waldheim, Buchmüller)
