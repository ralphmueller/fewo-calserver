uwsgi --http-socket :5000  --module wsgi:app  --virtualenv /Users/ralph/.local/share/virtualenvs/fewo-calserver-dnC1dOzX

# Installation

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

% sind wildcard Zeichen

Müller - findet alle mit Nachnamen Müller
%Müller - findet alle, deren Namen auf Müller endet (Eide-Müller, Buchmüller)
Müller% - findet alle, deren Namen mit Müller beginnt (Müller-Waldheim, Müller - Testbenutzer)
%Müller% - findet alle, in deren Namen das Wort Müller vorkommt (von Müller-Meier, Müller, Müller-Waldheim, Buchmüller)