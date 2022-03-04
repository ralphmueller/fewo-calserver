# Installation

## from bitbucket.org

### clone

    git clone https://ralph_mueller@bitbucket.org/ralph_mueller/fewo-calserver.git

or 

    git clone git@bitbucket.org:ralph_mueller/fewo-calserver.git

### change origin to ssh 

    git remote set-url origin git@bitbucket.org:ralph_mueller/fewo-calserver.git
    git remote -v

## node modules

    cd flaskr/static
    npm install

## pipenv

create pipenv for the required python version  and install

    pipenv --python 3.9
    ppipenv install

## pythonpacks

### create wheel 

    pipenv run  python setup.py sdist

### install on target

    pipenv install --skip-lock pythonpacks-<version>.tar.gz

## node_modules

## .env file

## test run

    pipenv run uwsgi --http-socket :5000  --module wsgi:application

## uwsgi conf (flaskr.ini)

Important: To avoid error like [mysql out of sync](https://github.com/PyMySQL/PyMySQL/issues/563) see link (https://stackoverflow.com/questions/22752521/uwsgi-flask-sqlalchemy-and-postgres-ssl-error-decryption-failed-or-bad-reco) use the fix below.

    [uwsgi]
    module = wsgi

    master = true
    processes = 5

    # the fix
    lazy = true
    lazy-apps = true

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

## Run as service /etc/systemd/system/fewo-calserver.service

Comments

Type=idle    - waits for everything else being started .. [link](https://superuser.com/questions/544399/how-do-you-make-a-systemd-service-as-the-last-service-on-boot/573761#573761)

Source

    [Unit]
    Description=uWSGI fewo-calserver
    After=syslog.target

    [Service]
    User=<user>
    WorkingDirectory=/home/<dir>/fewo-calserver

    # Linux Server Gersfeld
    ExecStart=/home/rmueller/.local/bin/pipenv run uwsgi --ini /home/rmueller/fewo-calserver/flaskr.ini
    # Rapspi
    # ExecStart=/home/pi/.local/bin/pipenv run uwsgi --ini /home/pi/fewo-calserver/flaskr.ini

    # Requires systemd version 211 or newer
    Restart=always
    KillSignal=SIGQUIT
    Type=idle
    StandardError=syslog
    NotifyAccess=all

    [Install]
    WantedBy=multi-user.target

# Bedienungsnotizen

## Besucher Suche

*** sind wildcard Zeichen

Müller - findet alle mit Nachnamen Müller
*Müller - findet alle, deren Namen auf Müller endet (Eide-Müller, Buchmüller)
Müller* - findet alle, deren Namen mit Müller beginnt (Müller-Waldheim, Müller - Testbenutzer)
*Müller* - findet alle, in deren Namen das Wort Müller vorkommt (von Müller-Meier, Müller, Müller-Waldheim, Buchmüller)
