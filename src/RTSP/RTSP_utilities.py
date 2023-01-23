import numpy as np
import config
from RTSP.data_classes.TPatient import TPatient
from RTSP.data_classes.Scenario import Scenario
from RTSP.data_classes.TRunResult import TResult, TRunResult
from typing import List, Tuple, Dict

WEIGHT_WAIT_BY_PRIORITY = {1: 10, 2: 10, 3: 1, 4: 1}  
WEIGHT_LATE_BY_PRIORITY = {1: 1000, 2: 1000, 3: 100, 4: 100}

def ensembleResult(_insName, _insPath, _solver: str, scenario_sol: Scenario, _runresult: TRunResult, _runtime: float,
                   _mipgap: float = 1, _noSimDay: int = config.NO_DAYS_SIMULATION) -> 'TResult':
    d_insinf = toDictInsInfor(scenario_sol, _noSimDay)
    _lNoPatients = [d_insinf['P'], d_insinf['P1'], d_insinf['P2'], d_insinf['P3'], d_insinf['P4']]
    _lNoNewPatients = [d_insinf['Pnew'], d_insinf['P1new'], d_insinf['P2new'], d_insinf['P3new'], d_insinf['P4new']]
    _lNoSections = [
        sum([d_insinf['noSectionsP1'], d_insinf['noSectionsP2'], d_insinf['noSectionsP3'], d_insinf['noSectionsP4']]),
        d_insinf['noSectionsP1'], d_insinf['noSectionsP2'], d_insinf['noSectionsP3'], d_insinf['noSectionsP4']]
    
    lOccupancy = scenario_sol.getOccupancyRateByDay_ByPriority(_noSimDay)
    _runresult.update_occupandy(lOccupancy)

    name_short = _insName.split('_')[0]
    result = TResult(ins_name=name_short, ins_path=_insPath, solver=_solver, simdays=d_insinf['simdays'],
                     noLinacs=d_insinf['noLinacs'],
                     arrivalrate=d_insinf['lambda'], noSlotsPerDay=d_insinf['S'], planningHorizon=d_insinf['T'],
                     lNoPatients=_lNoPatients, lNoNewPatients=_lNoNewPatients, lNoSections=_lNoSections,
                     runresult=_runresult, runtime=_runtime, mipgap=_mipgap)
    return result

def toDictInsInfor(sce: Scenario, noSimDay):
    ''''''
    infor = {}
    
    lPatients = [p for p in sce.lPatients if p.admissionDay < noSimDay]
    lCount_Patient = getNoPatients_ByCategory(lPatients)  # self.getNoPatientsByPriority()
    lNewPatients = [p for p in lPatients if p.admissionDay >= 0]  # scenario.getListOfNewPatients()
    lCount_NewPatient = getNoPatients_ByCategory(lNewPatients)  # self.getNoNewPatients()
    lCount_noSectionsNewP = getNoSections(lNewPatients)  # self.getNoSections()

    scap = ['instance', 'simdays', 'P', 'lambda', 'noLinacs', 'S', 'T', 'Pnew',
            'P1', 'P2', 'P3', 'P4',
            'P1new', 'P2new', 'P3new', 'P4new', 'noSectionsP1', 'noSectionsP2', 'noSectionsP3', 'noSectionsP4']
    
    
    noFixedPatients = lCount_Patient[0]  # - lCount_NewPatient[0]
    
    sinfor = [sce.name, noSimDay, noFixedPatients, sce.arrivalRate, sce.noLinacs,
              sce.single_linac_capacity,
              sce.planningHorizon, lCount_NewPatient[0],  # self._planningScope,
              lCount_Patient[1], lCount_Patient[2], lCount_Patient[3], lCount_Patient[4],
              lCount_NewPatient[1], lCount_NewPatient[2], lCount_NewPatient[3], lCount_NewPatient[4],
              lCount_noSectionsNewP[1], lCount_noSectionsNewP[2], lCount_noSectionsNewP[3],
              lCount_noSectionsNewP[4]]
    for (i, key) in enumerate(scap):
        infor[key] = sinfor[i]
    return infor

def getNoSections(lPatients: List[TPatient]):
    '''return a list of 5, the first value is total number of sections of new patients
    the next 4 is by priority'''
    lcount = np.full(5, 0)
    for i, p in enumerate(lPatients):
        lcount[0] = lcount[0] + p.noSections
        for priority in range(1, 5):
            if p.priority == priority:
                lcount[priority] = lcount[priority] + p.noSections
    return lcount

def getNoPatients_ByCategory(lPatients: List[TPatient]):
    '''return a list of 5, the first value is total number of new patients
    the next 4 is by priority'''
    lcount = np.full(5, 0)
    for i, p in enumerate(lPatients):
        lcount[0] = lcount[0] + 1
        for priority in range(1, 5):
            if p.priority == priority:
                lcount[priority] = lcount[priority] + 1
    return lcount

def removedPatientsFromList(lPatients: List[TPatient], lId_tobemoved: List[int]) -> List[TPatient]:
    '''remove patients from lPatients_tobemoved from lPatients
    return the new list (but also modify the parameter'''
    for i in range(len(lPatients) - 1, -1, -1):
        if(lPatients[i].index in lId_tobemoved):
            lPatients.remove(lPatients[i])
    return lPatients

# def isInListOfPatients(lPatients: List[TPatient], pIndex):
#     '''check if patient with pIndex exists in list patients'''
#     lPatientIdx = [p.index for p in lPatients]
#     if pIndex in lPatientIdx:
#         return True
#     return False

def getNoSimDays(lPatients: List[TPatient]) -> Tuple[int, int]:
    '''return the first and last admission days'''
    if(len(lPatients) == 0):
        return (-1,-1)
    lDays = [p.admissionDay for p in lPatients]
    _min = min(lDays)
    _max = max(lDays)
    return (_min, _max)

# def get_Information_NewPatients(lPatients: List[TPatient], infor: str):
#     ''' infor takes values of 'admissionDay'
#     return 5 arrays
#     the first one is infor of all patients
#     the next 4 ones are infor of patients by category'''
#     # admissionDay, duration, noSections
#     lAll = []
#     if(infor == 'admissionDay'):
#         lAll = [p.admissionDay for p in lPatients]
#     elif(infor == 'duration'):
#         lAll = [p.duration for p in lPatients]
#     elif(infor == 'noSections'):
#         lAll = [p.noSections for p in lPatients]
#     else:
#         print('error', infor, 'is not supported - get_Information_NewPatients')
#     lInfor = []
#     for i in range(0,5):
#         lInfor.append([])
#     for i, p in enumerate(lPatients):
#         lInfor[0].append(lAll[i])
#         for priority in range(1,5):
#             if lPatients[i].priority == priority:
#                 lInfor[priority].append(lAll[i])
#     return lInfor


# def getListOfValidStartingDaysAndLinac(scenario: Scenario, p: TPatient, reserveLinac: bool,
#                                        _predicted_day: int, _search_width: int, reservation_rate: float) -> List[Tuple[int, int]]:
#     '''given a scenario and a patient, return a list of valid starting days and linacs for that patients
#     if there are many valid linacs a day, return only the first one
#     only return (less than or) a (_search_width) number of days with (center) as the median
#     used in MCTS'''
#     capacity = scenario.single_linac_capacity
#     if (reserveLinac == True):
#         if (int(p.priority) >= 3):  # '3' or priority == '4'):          # curative
#             capacity = scenario.single_linac_capacity * reservation_rate
#     lValidOptions = []
#     max_late_day_allowed = config.PAR_MAX_LATE_ALLOWED[p.priority]
#     # endday = min(scenario.planningScope, p.admissionDay + max_late_day_allowed)
#     day_backward = _predicted_day
#     day_forward = _predicted_day + 1
#     while(len(lValidOptions) < _search_width):
#         if(day_backward >= p.releaseDay):
#             for linac in range(0, scenario.noLinacs):
#                 if all(o <= (capacity - p.duration) for o in
#                        scenario._occupancy[day_backward:day_backward + p.noSections, linac]):
#                     lValidOptions.append((day_backward, linac))
#                     break
#             day_backward = day_backward - 1
#         if(day_forward <= scenario.planningScope + 100):
#             for linac in range(0, scenario.noLinacs):
#                 if all(o <= (capacity - p.duration) for o in
#                        scenario._occupancy[day_forward:day_forward + p.noSections, linac]):
#                     lValidOptions.append((day_forward, linac))
#                     break
#             day_forward = day_forward + 1
#         if(day_backward < p.releaseDay and day_forward > (scenario.planningScope + 100)):
#             break
#     return lValidOptions

def findTheFirstValidDayAndLinac(scenario: Scenario, startday: int, p: TPatient, percentage_nonreserved: float) -> Tuple[int, int]:
    capacity = scenario.single_linac_capacity
    # if (percentage_nonreserved == True):
    if (int(p.priority) >= 3):  # '3' or priority == '4'):          # curative
        capacity = scenario.single_linac_capacity * percentage_nonreserved
    valid_sday = -1
    valid_linac = -1
    for day in range(startday, scenario.planningScope):
        for linac in range(0, scenario.noLinacs):
            if all(o <= (capacity - p.duration) for o in scenario._occupancy[day:day + p.noSections, linac]):
                valid_sday = day
                valid_linac = linac
                break
        if (valid_sday > -1):
            break
    return (valid_sday, valid_linac)

def getDictPatientsByDate(lPatients: List[TPatient]) -> Dict[int, List[TPatient]]:
    '''return a dictionary, key is addmission date
            value is list of patient admitted on that date'''
    lPatientsByDay = {}
    for p in lPatients:
        if (p.admissionDay not in lPatientsByDay.keys()):
            lPatientsByDay[p.admissionDay] = []
        lPatientsByDay[p.admissionDay].append(p)
    return lPatientsByDay

def schedulePatientFeasibly(scenario:Scenario, startday: int, p: TPatient, percentage_nonreserved: float) -> Tuple[int, int]:
    '''find a day after startday to insert patient feasibly,
    add patient to scenario
    return patient's startday and linac
    '''
    valid_sday, valid_linac = findTheFirstValidDayAndLinac(scenario, startday, p, percentage_nonreserved)
    if(valid_sday == -1):
        print('ERROR cant find a valid start day for patient ', p.index)
    # found, then update scenario
    scenario.schedulePatient(p, valid_sday, valid_linac, p.noSections)
    return valid_sday, valid_linac

# def evaluateSolution_obj(scenario: Scenario):
#     '''return a single objective value
#     solution must be feasible already when this function is called'''
#     lPatients = scenario.getListOfNewPatients()
#     tresult = evaluateSolution(scenario, lPatients, checkFeasibility=False, verbal=False)
#     obj = tresult.objval
#     return obj


def evaluateSolution(scenario: Scenario,
                     lPatients: List[TPatient] = None,
                     checkFeasibility: bool = True,
                     verbal: bool = True) -> 'TRunResult.py':
    '''note that calculate wait day and late day taking weekend into account
    current day is 2021-03-01 for all instances, for now
    return average waiting day, late day and feasibility'''
    if(lPatients == None):
        lPatients = scenario.getListOfNewPatients()
    lAdmissionDays = [p.admissionDay for p in lPatients]
    lPriority = [p.priority for p in lPatients]
    l_noPatients = getNoPatients_ByCategory(lPatients)
    l_wait_day = scenario.getListWaitDay(lPatients)         # 5 array
    l_late_day = scenario.getListLateDay(lPatients)

    lwaitday_by_priority = [sum(x) for x in l_wait_day]    #[1:]
    llateday_by_priority = [sum(x) for x in l_late_day]    #[1:]
    l_nopatients_without0 = [max(a, 1) for a in l_noPatients]       # to calculate average values
    l_avg_waitday_by_priority = [i/j for i, j in zip(lwaitday_by_priority,l_nopatients_without0)]
    l_avg_lateday_by_priority = [i/j for i, j in zip(llateday_by_priority,l_nopatients_without0)]

    feasibility = None
    if (checkFeasibility == True):
        feasibility = scenario.check_sce_integrity(verbal = verbal)

    # calculate objective here
    obj = 0
    for i in range(1, 5):
        obj += l_avg_waitday_by_priority[i] * WEIGHT_WAIT_BY_PRIORITY[i]
        obj += l_avg_lateday_by_priority[i] + WEIGHT_LATE_BY_PRIORITY[i]

    lWaitAndOverdue = [(admissionday, pri, wait, overdue) for admissionday, pri, wait, overdue 
                                in zip (lAdmissionDays, lPriority, l_wait_day[0],l_late_day[0])]
    tresult = TRunResult(feasibility=feasibility,
                         objval=obj,
                         lWaitDayByPriority=lwaitday_by_priority,
                         lLateDayByPriority=llateday_by_priority,
                         lAvgWaitDayByPriority=l_avg_waitday_by_priority,
                         lAvgLateDayByPriority=l_avg_lateday_by_priority, 
                         lWaitAndOverdue=lWaitAndOverdue)

    return tresult

# def toStringStartAndLateDays(scenario: Scenario, lPatients: List[TPatient],
#                       onlyPalliative: bool = False,
#                       onlyLate: bool = True):
#     if (lPatients == None):
#         lPatients = scenario.getListOfNewPatients()
#     # l_noPatients = getNoPatients_ByCategory(lPatients)
#     s = ''
#     for p in lPatients:
#         if(p.admissionDay <= -1):
#             continue
#         if(onlyPalliative == True and p.isPalliative() == False):
#             continue
#         startday = scenario.getStartDayOfPatient(p.index)
#         waitday = mydatetime.getDistanceBetweenRelativeDays(p.admissionDay, startday)
#         lateday = mydatetime.getDistanceBetweenRelativeDays(p.dueDay, startday) if(startday > p.dueDay) else 0
#         if(onlyLate == True and lateday == 0):
#             continue
#         s += '{} - admission {} - ready {} - start {} - wait {} - late {}\n'.format(p, p.admissionDay, p.releaseDay,
#                                                                     startday, waitday, lateday)
#     return s

# def toStringInsInfor(scenario: Scenario, lPatients: List[TPatient]):

#     scap = ['Instance infor', 'simulationdays', 'P', 'lambda', 'K', 'S', 'T', 'scope', 'Pnew','currentday','','P1', 'P2', 'P3','P4',
#             'newP1', 'newP2', 'newP3', 'newP4','noSectionsP1','noSectionsP2','noSectionsP3','noSectionsP4']
#     currentday = 0      # I hope?
#     stupidstuff = 3
#     lCount_Patient = getNoPatients_ByCategory(scenario.lPatients)  # self.getNoPatientsByPriority()
#     lNewPatients_FromScenario = scenario.getListOfNewPatients()
#     lNewPatients_both = lNewPatients_FromScenario + lPatients
#     lCount_NewPatient = getNoPatients_ByCategory(lNewPatients_both)  # self.getNoNewPatients()
#     lCount_noSectionsNewP = getNoSections(lNewPatients_both)  # self.getNoSections()
#     noFixedPatients = lCount_Patient[0] - lCount_NewPatient[0]
#     (min_day, max_day) = getNoSimDays(lNewPatients_both)

#     sinfor = [scenario.name, (max_day - min_day + 1), noFixedPatients,
#               scenario.arrivalRate, scenario.noLinacs, scenario.single_linac_capacity,
#               scenario.planningHorizon, scenario.planningScope,
#               lCount_NewPatient[0], currentday, stupidstuff,
#               lCount_Patient[1], lCount_Patient[2], lCount_Patient[3], lCount_Patient[4],
#               lCount_NewPatient[1], lCount_NewPatient[2], lCount_NewPatient[3], lCount_NewPatient[4],
#               lCount_noSectionsNewP[1], lCount_noSectionsNewP[2], lCount_noSectionsNewP[3], lCount_noSectionsNewP[4]]
#     s = ', '.join(
#         ':'.join(str(a) for a in list(tuple)) for tuple in list(zip(scap, sinfor))
#     )
#     s = s + '\n'
#     return s


