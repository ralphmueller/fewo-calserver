# todo list


## Home

* list arrivals
* list departures 
* list offers

## Buchung
* preferred language templates for email to besucher
* personalize templates with user info 
* creation: set user

### Vorauszahlung

* create html and WTForm
* finish buchung.vorauszahlung
    * save
    * send email to visitor
    * send email to team

## User

* user change password

### Besucher
* creation: set user
* update: set userlastupdate

### Buchung
* update/storno/vorauszahlung/abrechnen: set userlastupdate

## User

* extend schema (name, first_name, title, password last changed, role)

## Deployment

some comments: 

* experimented with uwsgi on MBPro

    uwsgi --http-socket :5000  --module wsgi:app  --virtualenv /Users/ralph/.local/share/virtualenvs/fewo-calserver-dnC1dOzX

* nginx - trying soon

TBD 

## MarkDown Strike

~~strike~~ - use double tilde


# Bugs

## Susan

* Not a valid integer value

* ~~Prüfen, ob Wohnung frei ist~~ added buttoon and related js to check (buchung.js)