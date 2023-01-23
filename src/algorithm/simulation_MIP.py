import config
from RTSP.data_classes.Scenario import Scenario, TPatient
from RTSP.data_classes.TRunResult import TRunResult
from RTSP.RTSP_utilities import ensembleResult
import RTSP.RTSP_utilities as rtsp_utils
import RTSP.readwriteUtils as rw
import algorithm.LPmodel as LP
from copy import deepcopy
from typing import List, Tuple

import time

def isAScheduledDay(day, solver) -> bool:
    '''for periodically scheduling - daily, biweekly or weekly'''
    if(solver == 'daily'):
        return True
    elif(solver == 'biweekly'):
        if (day%5 == 2 or day%5 ==4):
            return True
        else:
            return False
    elif (solver == 'weekly'):
        if (day % 5 == 4):
            return True
        else:
            return False
    return True

def solve_hybrid(scenario: Scenario, lPatients: List[TPatient], day_start, day_end,
                 config, static_version) -> Tuple[Scenario, LP.LPmodel]:
    ''' solve static version
    first, schedule all palliative patients
    then schedule curative patients using the LP model '''
    lIDScheduledPatients = []

    # schedule palliative patients and update new_ins
    for (i, p) in enumerate(lPatients):
        if(day_start <= p.admissionDay and p.admissionDay <= day_end):
            if (p.isPalliative()):
                startday, linac = rtsp_utils.schedulePatientFeasibly(scenario, p.releaseDay, p, config.reservation_rate)
                lIDScheduledPatients.append(p.index)

    rtsp_utils.removedPatientsFromList(lPatients, lIDScheduledPatients)

    # solve the LP model with the new instance
    lpmodel = LP.LPmodel.build_model(scenario, lPatients, day_start, day_end, config, static_version)
    if(lpmodel != None):
        scenario = lpmodel.solve()  # Solve the model and print solution
        return (lpmodel.result_sol, lpmodel)
    return (scenario, None)

def schedule_periodically(scenario: Scenario, lPatients: List[TPatient], conf) -> Scenario:
    firstsimday, lastsimday = rtsp_utils.getNoSimDays(lPatients) #original_ins._noSimDays
    # print('sim days {}- {}'.format(firstsimday, lastsimday))
    last_schedule = -1

    for day in range(0, lastsimday + 1):
        if isAScheduledDay(day, conf.solver) == True or day == lastsimday:
            print('\t~~scheduling period [{},{}]'.format(last_schedule + 1, day))
            (sol, lpmodel) = solve_hybrid(scenario, lPatients, last_schedule + 1, day,
                                          config=conf, static_version=False)

            last_schedule = day
    return scenario

# ----------------------------------------------------------------------------
# Solve the model and display the result
# ----------------------------------------------------------------------------
def runExprStatic(scenario: Scenario, lPatients: List[TPatient], conf) -> Tuple[Scenario, TRunResult, float]:
    lPatients_Selected = [p for p in lPatients if p.admissionDay < conf.simday or p.isPalliative()]
    lPatients_changed = deepcopy(lPatients_Selected)
    sol, lpmodel = solve_hybrid(scenario, lPatients_changed, 0, 100, config=conf, static_version=True)
    mipgap = lpmodel.result_gap

    # here, the weird thing, you evaluate it with a different set of patients, to match with other strategies
    lPatients_Evaluate = [p for p in lPatients if p.admissionDay < conf.simday]
    runresult = rtsp_utils.evaluateSolution(sol, lPatients_Evaluate, checkFeasibility=True, verbal=False)
    return sol, runresult, mipgap

def runExprPeriodic(scenario: Scenario, lPatients: List[TPatient], conf) -> Tuple[Scenario, TRunResult, float]:
    lPatients_Selected = [p for p in lPatients if p.admissionDay < conf.simday]
    lPatients_changed = deepcopy(lPatients_Selected)
    mipgap = 1.0
    sol = schedule_periodically(scenario, lPatients_changed, conf)

    runresult = rtsp_utils.evaluateSolution(sol, lPatients_Selected, checkFeasibility=True, verbal=False)
    return sol, runresult, mipgap

def solveOneInstance(insfile, solfile, resultfile, alg, noSimDay = None):
    '''to solve real instance file'''
    print('solving {} \n alg {}'.format(insfile, alg))
    conf = config.get_config()
    if(noSimDay != None):
        conf.simday = noSimDay
    conf.solver = alg # static, weekly, biweekly, daily
    scenario, lPatients = rw.read_instance_rtsp(insfile)
    start = time.time()

    if(alg in ['static', 'static2']):
        sol, runresult, mipgap = runExprStatic(scenario, lPatients, conf)
    else:
        sol, runresult, mipgap = runExprPeriodic(scenario, lPatients, conf)

    run_time = time.time() - start
    result = ensembleResult(scenario.name, conf.ins_path, _solver=alg, scenario=sol,
                                    _runresult=runresult, _runtime= run_time, _noSimDay=conf.simday)
    sol.saveSolToFile(output_path=solfile)
    result.save_result(resultfile)

    sol.check_sce_integrity()

