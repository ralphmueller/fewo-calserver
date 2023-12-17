
'''
Created on 28.08.2022

@author: ralph

snippets

'''
import datetime


def get_monday_of_week(a_date):
    '''
        return the date of the monday of the week for a given date
    '''
    week_str = "{}-W{}".format(
        a_date.isocalendar().year, a_date.isocalendar().week)
    return datetime.datetime.strptime(week_str + '-1', "%Y-W%W-%w")

