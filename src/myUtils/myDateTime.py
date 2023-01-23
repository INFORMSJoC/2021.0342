import datetime
from datetime import date, datetime, timedelta
import math


def fromStringToDate(str, format):
    # TODO: actually, should change base on the stuff
    if (str == ''):
        return None
    if(str == 'None'):
        return None
    if(str == '-'):
        return None
    day = datetime.strptime(str, format)
    return day


def getDistanceBetweenRelativeDays(startday: int, endday: int):

    baseday = date(day=1, month=3, year=2021)               # actually it doesn't matter here, it's distance in days, not business days
    startday_withwk = startday + 2 * int(math.floor(startday/5))            # given that day 0 is a Monday
    endday_withwk = endday + 2 * int(math.floor(endday/5))
    startdate = baseday + timedelta(days=int(startday_withwk))
    enddate = baseday + timedelta(days=int(endday_withwk))
    return (enddate - startdate).days
