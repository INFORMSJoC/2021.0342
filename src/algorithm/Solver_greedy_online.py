from algorithm.Solver_prediction_base import Solver_prediction_base
from typing import List
import RTSP.RTSP_utilities as rtsp_utils
import myUtils.myDateTime as mydatetime


class Solver_greedy_online(Solver_prediction_base):
    def __init__(self, scenario: 'Scenario', lPatients: List['TPatient'], loaded_model, reservation_rate, regression_mode, config = None) -> None:
        super().__init__(scenario, lPatients, loaded_model, reservation_rate, regression_mode, config)
    
    def solve(self) -> 'Scenario':
        sumwaitday = 0

        for (i, p) in enumerate(self.lPatients):

            startday = p.releaseDay
            if (p.isPalliative() == False):           # if curative, find 1 or 2 weeks ahead
                startday = p.admissionDay + (int)((p.dueDay - p.admissionDay) / 2)
                startday = max(startday, p.releaseDay)
            valid_startday, valid_linac = rtsp_utils.schedulePatientFeasibly(self.scenario, startday, p, self.reservation_rate)
            waitday = mydatetime.getDistanceBetweenRelativeDays(p.admissionDay, valid_startday)
            sumwaitday = sumwaitday + waitday

        return self.scenario