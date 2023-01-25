from copy import deepcopy
from algorithm.Solver_prediction_base import Solver_prediction_base
from typing import List
import RTSP.RTSP_utilities as rtsp_utils
import myUtils.common as cm


class Solver_greedy_daily(Solver_prediction_base):
    def __init__(self, scenario: 'Scenario', lPatients: List['TPatient'], loaded_model, reservation_rate, regression_mode, config = None) -> None:
        super().__init__(scenario, lPatients, loaded_model, reservation_rate, regression_mode, config)
    
    def solve(self) -> 'Scenario':
        (min_sim, max_sim) = rtsp_utils.getNoSimDays(self.lPatients)
        occupancy = self.scenario.getOccupancyByDay()
        remaining_cap = (self.scenario.noLinacs * self.scenario.single_linac_capacity) - occupancy
        last_schedule = -1

        for day in range(0, max_sim + 1):
            l_patients_in_batch = []

            if(day % 10 == 0):
                print('~~~~~~~~~~~~~~~~~~~~~~~~~scheduling period [{},{}]'.format(last_schedule + 1, day))

            for i, p in enumerate(self.lPatients):
                if p.admissionDay == day:
                    if p.isPalliative() == False:                    # curative          - batch them to schedule later
                        l_patients_in_batch.append(p)
                    else:                                               # palliative    - schedule them right away
                        valid_sday, valid_linac = rtsp_utils.schedulePatientFeasibly(   self.scenario, 
                                                                                    p.releaseDay, 
                                                                                    p,
                                                                                    percentage_nonreserved=self.reservation_rate)
                        cm.updateRemainingCapacity( remaining_cap, startday=valid_sday, noSections=p.noSections, duration=p.duration)
            self.schedule_patients(l_patients_in_batch, remaining_cap)        
            last_schedule = day

        return self.scenario
    
    def schedule_patients(self, l_patients: List['TPatient'], remaining_cap):
        '''schedule a batch of patients'''
        accumulated_cap = deepcopy(remaining_cap)
        self.sort_patients(l_patients)

        for p in l_patients:
            start_day = p.admissionDay + (int)((p.dueDay - p.admissionDay) / 2)
            valid_sday, valid_linac = rtsp_utils.schedulePatientFeasibly(   self.scenario, start_day, p, self.reservation_rate)
            cm.updateRemainingCapacity(         accumulated_cap,  
                                                startday=valid_sday,
                                                noSections=p.noSections, 
                                                duration=p.duration)

        remaining_cap = accumulated_cap
    
    def sort_patients(self, l_patients: List['TPatient']):
        '''sort patients before schedule them using greedy algorithm
        P3 > P4
        difficult patients are prioritized (duration, noSections)'''
        # calculate a score for each patient
        dict_weight_priority = {3: 1000, 4: 0}
        scores = []
        for p in l_patients:
            scores.append(dict_weight_priority[p.priority] + p.duration * p.noSections)
        
        l_patients = [p for score,p in sorted(zip(scores,l_patients), key=lambda x: x[0], reverse=True)]
        return l_patients