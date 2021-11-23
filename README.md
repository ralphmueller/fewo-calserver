uwsgi --http-socket :5000  --module wsgi:app  --virtualenv /Users/ralph/.local/share/virtualenvs/fewo-calserver-dnC1dOzX

uwsgi  --socket 0.0.0.0:5000 --protocol=http  --module wsgi:app --virtualenv /Users/ralph/.local/share/virtualenvs/fewo-calserver-dnC1dOzX
