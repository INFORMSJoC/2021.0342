
from RTSP.data_classes.Scenario import Scenario, TPatient
from RTSP.data_classes.TRunResult import TRunResult
import RTSP.RTSP_utilities as rtsp_Utils
import RTSP.readwriteUtils as readwrite
import myUtils.myDateTime as mydatetime
from typing import List, Tuple
import config
import time
from RTSP.RTSP_utilities import ensembleResult


def construct_solution(sce:Scenario, lPatients: List[TPatient], percentage_nonreserved: float) -> Scenario:
    '''construct solution heuristically, the way CHUM does for each patient, look ahead 1 or 2 weeks'''
    sumwaitday = 0
    for (i, p) in enumerate(lPatients):
        startday = p.releaseDay
        if (p.isPalliative() == False):           # if curative, look 1 or 2 weeks ahead
            startday = p.admissionDay + (int)((p.dueDay - p.admissionDay) / 2)
            startday = max(startday, p.releaseDay)
        valid_startday, valid_linac = rtsp_Utils.schedulePatientFeasibly(sce, startday, p, percentage_nonreserved)
        waitday = mydatetime.getDistanceBetweenRelativeDays(p.admissionDay, valid_startday)
        sumwaitday = sumwaitday + waitday

    return sce


def runExpr(    scenario: Scenario, 
                lPatients: List[TPatient], 
                conf
            ) -> Tuple[Scenario, TRunResult]:
    lPatients_Selected = [p for p in lPatients if p.admissionDay < conf.simday]
    
    sol = construct_solution(scenario, lPatients_Selected, percentage_nonreserved=conf.reservation_rate)
    runresult = rtsp_Utils.evaluateSolution(sol, lPatients_Selected, checkFeasibility=True, verbal=False)
    return (sol, runresult)

def solveOneInstance(insfile, solfile, resultfile, alg,  noSimDay = None):
    '''to solve real instance file'''
    print('solving {} \n alg {}'.format(insfile, alg))
    conf = config.get_config()
    if (noSimDay != None):
        conf.simday = noSimDay
    conf.solver = alg
    scenario, lPatients = readwrite.read_instance_rtsp(insfile)
    start = time.time()

    sol, runresult = runExpr(scenario, lPatients, conf)

    run_time = time.time() - start
    
    result = ensembleResult(scenario.name, insfile, conf.solver, sol, runresult, run_time, 0, conf.simday)

    sol.saveSolToFile(output_path=solfile)
    result.save_result(resultfile)

    sol.check_sce_integrity()


