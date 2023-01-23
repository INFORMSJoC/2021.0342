from algorithm.Solver_prediction_base import Solver_prediction_base
from typing import List
import RTSP.RTSP_utilities as rtsp_utils
import myUtils.common as cm

class Solver_prediction_online (Solver_prediction_base):
    
    def __init__(self, scenario: 'Scenario', lPatients: List['TPatient'], loaded_model, reservation_rate, regression_mode, config = None) -> None:
        super().__init__(scenario, lPatients, loaded_model, reservation_rate, regression_mode, config)
    
    def solve(self) -> 'Scenario':
        '''solve instance using regression method - hybrid method - palliative patients asap, curative regression
        change the input scenario?
        return the resuling scenario'''
        (min_sim, max_sim) = rtsp_utils.getNoSimDays(self.lPatients)
        occupancy = self.scenario.getOccupancyByDay()
        remaining_cap = (self.scenario.noLinacs * self.scenario.single_linac_capacity) - occupancy

        for day in range(0, max_sim + 1):
            for i, p in enumerate(self.lPatients):
                if p.admissionDay == day:
                    predict_start_day = p.releaseDay                # palliative
                    if p.isPalliative() == False:                    # curative
                        predict_waitday = self.predict_waitTime_onlinescheduling(p, remaining_cap)
                        predict_start_day = day + predict_waitday
                        if (predict_start_day < p.releaseDay):
                            predict_start_day = p.releaseDay

                    valid_sday, valid_linac = rtsp_utils.schedulePatientFeasibly(   self.scenario, 
                                                                                    predict_start_day, 
                                                                                    p,
                                                                                    percentage_nonreserved=self.reservation_rate)
                    cm.updateRemainingCapacity( remaining_cap, 
                                                startday=valid_sday,
                                                noSections=p.noSections, 
                                                duration=p.duration)

        return self.scenario
