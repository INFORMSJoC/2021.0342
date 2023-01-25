import numpy as np

def findAnEligibleStartDay_LinacSpecific(startday, lOccupancy, linacCap, noSections, duration):
    '''find the first eligible day after the given startday
    return start day and linac as well'''
    valid_sday= -1
    valid_linac = -1
    for day in range(startday, len(lOccupancy)):

        for linac in range(0, len(lOccupancy[day])):

            if all(o <= (linacCap-duration) for o in lOccupancy[day:day+noSections, linac]):
                valid_sday = day
                valid_linac = linac    
                break

        if(valid_sday > -1):
            break
    if (valid_sday == -1):
        valid_sday = len(lOccupancy)
        valid_linac = 0
        
    return valid_sday, valid_linac

def updateOccupancyLinacSpecific(current_occupancy, startday, linac, noSections, duration):
    '''given current occupancy, update occ starting from startday with a given duration and number of sections on a specific linac
        return new occupancy'''
    newoccupancy = current_occupancy.copy()
    endday = min(len(newoccupancy), startday + noSections)  # self._ins._listPatients[patient]['noSections'])
    for d in range(startday, endday):
        newoccupancy[d, linac] = newoccupancy[d, linac] + duration  # self._ins._listPatients[patient]['duration']
    return newoccupancy

def updateRemainingCapacity(current_capacity, startday, noSections, duration):
    endday = min(len(current_capacity), startday + noSections)  # self._ins._listPatients[patient]['noSections'])
    for d in range(startday, endday):
        current_capacity[d] = current_capacity[d] - duration  # self._ins._listPatients[patient]['duration']
    return current_capacity
    
def updateOccupancy(current_occupancy, startday, noSections, duration):
    '''given current occupancy, update occ starting from startday with a given duration and number of sections
    return new occupancy'''
    endday = min(len(current_occupancy), startday + noSections) # self._ins._listPatients[patient]['noSections'])
    for d in range(startday, endday):
        current_occupancy[d] = current_occupancy[d] + duration # self._ins._listPatients[patient]['duration']
    return current_occupancy

def groupSumValuesByWeek(lDays, lValues):

    noWeeks = int((max(lDays) + 4)/5)
    lSum = np.zeros(noWeeks)
    lCount = np.zeros(noWeeks)
    for (i, day) in enumerate(lDays):
        week = int(day/5)
        lSum[week] = lSum[week] + lValues[i]
        lCount[week] = lCount[week] + 1

    lAverage = np.divide(lSum, lCount)
    return lCount, lSum, lAverage

