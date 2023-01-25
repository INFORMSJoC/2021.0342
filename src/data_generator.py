import random
import numpy as np
from typing import List, Tuple
from RTSP.data_classes.Scenario import TAppointment,  TPatient
import myUtils.common as cm


def modifiedPoissonGenerator(arrivalrate, n, seed = None):
    '''generate arrivals following the given arrivalrate
    cut off irregular values which are > 2*arrivalrate'''
    if(seed != None):
        np.random.seed(seed)
    arrivals = np.random.poisson(arrivalrate, n)
    for (i, a) in enumerate(arrivals):  # cut off irregular values
        if (a > arrivalrate * 2):
            arrivals[i] = arrivalrate * 2
    return arrivals

def createAppsFromKnapsack(lAssignments: List[Tuple[int, TPatient]], noLinacs: int, noSlot: int, scopeInDay: int
) -> Tuple[bool, List[TAppointment]]:
    '''lAssignments item is a tuple (day, TPatient)
    :return a list of TAppointment'''
    lResults = []
    occupancy = np.zeros((scopeInDay + 300, noLinacs), dtype=int)
    linac = 0
    appstart = 0
    lAssByDay = []                          # build a list of assignments by days first
    for (day, patient) in lAssignments:           #day = item[0]        pIndex = item[1]
        if(day >= len(lAssByDay)):
            lAssByDay.append([patient])
        else:
            lAssByDay[day].append(patient)
    for day in range(0, len(lAssByDay)):
        totalDuration = 0
        for (i, p) in enumerate(lAssByDay[day]):
            duration = p.duration # int(lPatients[pIndex][9])
            totalDuration = totalDuration + duration
            found = False
            for k in range(0, noLinacs):
                if occupancy[day][k] + duration <= noSlot:
                    linac = k
                    appstart = occupancy[day][k]
                    occupancy[day][k] = occupancy[day][k] + duration
                    found = True
                    break
            if(found == False):                  # if can not find, will be so dead wrong here
                print("~~~~~~~~~~~~~~~ALERT cant find a valid spot day {} patient {} totalDur {}".format
                      (day, p.index, totalDuration))
                return found, lResults
            lResults.append(TAppointment(day, linac, p, appstart, appstart + duration-1))
    lResults.sort(key=lambda x: x.day)
    return found, lResults


def findAnEligibleStartDay(startday, lOccupancy, capacity, noSections, duration):
    '''find the first eligible day after the given startday'''
    valid_sday = -1
    for day in range(startday, len(lOccupancy)):
        if all(o <= (capacity-duration) for o in lOccupancy[day:day+noSections]):
            valid_sday = day
            break
    if (valid_sday == -1):
        valid_sday = len(lOccupancy)
    return valid_sday

def fillLinacs_withoutSpecificLinac(lPatientPoolItems, _lambda, capacity, nodays, respectCapacity, seed = None):
    '''start from an empty instance, keep taking patients, assigning random start day and linac
    until one day is full, then cut off the solution from the day after that'''
    
    occupancy = np.zeros(nodays + 300)
    lPatientIndex = []      
    lAdmissionDay=[]
    lStartDay = []
    arrivals = modifiedPoissonGenerator(_lambda, nodays, seed)
    pIndex = 0
    mapping_priority_dueday={'P1':0,'P2':2,'P3':8,'P4':16}
    mapping_priority_minday = {'P1': 0, 'P2': 0, 'P3': 4, 'P4': 10}
    for (day, noPatients) in enumerate(arrivals):
        for i in range (0, noPatients):
            p = lPatientPoolItems[pIndex]
            pIndex = pIndex + 1
            minday = mapping_priority_minday[p._urgency]
            dueday = mapping_priority_dueday[p._urgency]
            startday = random.randint(minday, dueday + 1) + day
            if(respectCapacity == True):
                startday = findAnEligibleStartDay(startday, occupancy, capacity, p._noSections, p._duration)
            
            cm.updateOccupancy(occupancy, startday, p._noSections, p._duration)
            lPatientIndex.append(p._patId)
            lAdmissionDay.append(day)
            lStartDay.append(startday)

    lAdmissionDay = np.array(lAdmissionDay)
    lStartDay = np.array(lStartDay)
    occupancy = np.array(occupancy)
    return lAdmissionDay, lStartDay, occupancy
