'''
Created on 10 Mar 2019

@author: ralph
'''

from flask import Blueprint, render_template, request
import datetime
import calendar

from bkormlib import envir
from bkormlib.schema import Apartment
from flaskr.auth import login_required

bp = Blueprint('calendar', __name__, url_prefix='')

@bp.route("/calendar")
@login_required
def routecalendar():
    today = datetime.date.today()
    year = int(request.args.get('year') or today.year)
    month = int(request.args.get('month') or today.month)
    # calculate prev/next month
    around = []
    if (month == 1):
        around.append ([12,year-1])
    else:
        around.append([month-1,year])
    if (month == 12):
        around.append ([1,year+1])
    else:
        around.append([month+1,year])  
    fewocalendar = FewoCalendar() 
    return render_template('calendar.html', around=around, month=month, year=year, days=days_in_month(year, month), data=fewocalendar.calendar_for_apartments(year, month), run_mode=envir)

class FewoCalendar():
    ''' 
        display a calendar for the holiday apartments
    '''
    def __init__(self):
        self.apartments = [apt for apt in Apartment.select()]
        
    def apartment_names(self):
        return sorted([apt.name for apt in self.apartments])
    
    def calendar_for_apartments(self, year, month):
        ''' 
            return an array that contains for every apartment a single list
            - name
            - 
        '''
        cal = [c for c in calendar.Calendar().itermonthdates(year, month)]
        result_list = []
        for apt in self.apartments:
            days = [0 for c in cal]
            av = [None for c in cal] # active visit for each day of the month, None if no visit
            html = ['' for c in cal] # active visit for each day of the month, None if no visit
            for active_visit in apt.calendar_support():
                # pass if it's not the current month
                if (active_visit.anreise > cal[-1]) or (active_visit. abreise < cal[0]):
                        pass
                else:
                    # this is inside
                    for i, day in enumerate(cal):
                        if day == active_visit.anreise:
                            days[i] += 2
                        if day == active_visit.abreise:
                            days[i] += 2
                        if (day > active_visit.anreise) and (day < active_visit.abreise):
                            days[i] = 1
                            av[i] = '{},{}:{}-{}'.format(active_visit.besucher.name, 
                                    active_visit.besucher.vorname, 
                                    active_visit.anreise.strftime('%d.%m.%y'), 
                                    active_visit.abreise.strftime('%d.%m.%y'))
                            html[i] = '<a href="/buchung/{}">&nbsp;</a>'.format(active_visit.id)
            result_list.append([{'apt': apt.name, 'day': d.day,'month' : d.month, 'year': d.year, 'weekday': d.isoweekday(),  'belegung':days[i], 'buchung':av[i], 'html':html[i]} for i, d in enumerate(cal)])
        return (result_list)
        
def days_in_month(year, month):
    DAYS_OF_WEEK = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa','So']
    c = calendar.Calendar()
    return [(f.day,DAYS_OF_WEEK[f.isoweekday()-1], f.month) for f in c.itermonthdates(year, month)]
