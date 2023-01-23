import math
from RTSP.data_classes.Scenario import Scenario, TPatient
import RTSP.RTSP_utilities as utils
from  myUtils import myDateTime as mydatetime
from docplex.mp.model import Model
import numpy as np
from typing import List

WEIGHT_WAIT_BY_PRIORITY={3: 1, 4:1} 
WEIGHT_LATE_BY_PRIORITY={3: 10000, 4:10000}
MIP_LOG_OUTPUT = False
MIP_GAP_THRESHOLD = 0.015

class LPmodel:
    model: Model
    scenario: Scenario
    lPatients_tobeScheduled: List[TPatient]
    day_begin: int              # solve the model for patients admitted in [day_begin, day_end]
    day_end: int

    reservation_rate: float
    # derived values
    noDays: int
    noNewPatients: int
    noLinacs: int

    # results
    result_time: float
    result_obj: float
    result_gap: float
    result_sol: Scenario

    def __init__(self, sce: Scenario, lPatients: List[TPatient], _day_begin: int, _day_end: int,
                 conf, static = True, **kwargs):
        '''schedule patients admitted during [_day_bgin, _day_end]
        the patient flow (lPatients) during the given period must not include palliative patients
        '''
        self.model = Model("RTSP", **kwargs)
        self.scenario = sce
        self.lPatients_tobeScheduled = lPatients
        self.day_begin = _day_begin
        (minSimDay,  maxSimDay) = utils.getNoSimDays(lPatients)
        self.day_end = min(_day_end, maxSimDay)

        self.STATIC_VERSION = static
        self.model.parameters.threads = conf.NO_THREADS
        self.model.parameters.timelimit = conf.timeout
        self.reservation_rate = conf.reservation_rate
        self.model.parameters.mip.tolerances.mipgap = MIP_GAP_THRESHOLD
        self.model.parameters.mip.display.set(1) # 0

    def setup_data(self):
        """ compute internal data """
        # derived section
        self.noDays = self.day_end - self.day_begin + self.scenario.planningHorizon + 1  # self.ins._planningScope
        self.noLinacs = self.scenario.noLinacs
        self.newPatients = []
        for i, p in enumerate(self.lPatients_tobeScheduled):
            if (self.day_begin <= p.admissionDay and p.admissionDay <= self.day_end):
                self.newPatients.append(p)
                assert (p.priority >=3)

        self.noNewPatients = len(self.newPatients)
        last_day = min(self.day_end + self.scenario.planningHorizon, self.scenario.planningScope)
        self.day_indices = list(range(self.day_begin, last_day))       #list(range(self.noDays))
        self.patient_indices = list(range(self.noNewPatients))
        self.linac_indices = list(range(self.noLinacs))
        return self.noNewPatients

    def setup_variables(self):
        # x[t,i,k] for each day t, new patient i, linac k
        self.model.x = self.model.binary_var_cube(self.day_indices, self.patient_indices,self.linac_indices, 'x')

    def setup_objective(self):
        lwaittime = np.zeros((self.scenario.planningScope, self.noNewPatients))      # for each day, patient
        loverdue = np.zeros((self.scenario.planningScope, self.noNewPatients))      # for each day, patient
        for (i, p) in enumerate(self.newPatients):
            for day in self.day_indices:
                lwaittime[day,i] = mydatetime.getDistanceBetweenRelativeDays(p.admissionDay, day)    if(day > p.admissionDay) else 0
                loverdue[day,i] = mydatetime.getDistanceBetweenRelativeDays(p.dueDay, day)           if(day > p.dueDay)       else 0
                lwaittime[day, i] = lwaittime[day, i] * math.log10(lwaittime[day,i] + 1)
                loverdue[day, i] = loverdue[day, i] * math.log10(loverdue[day,i] + 1)
        

        total_wait = self.model.sum(self.model.sum(self.model.x[t,i,k] * lwaittime[t,i]*WEIGHT_WAIT_BY_PRIORITY[self.newPatients[i].priority]
                                    for t in self.day_indices
                                    for i in self.patient_indices
                                    for k in self.linac_indices))

        total_overdue = self.model.sum(self.model.sum(self.model.x[t,i,k]* loverdue[t,i]*WEIGHT_LATE_BY_PRIORITY[self.newPatients[i].priority]
                                    for t in self.day_indices
                                    for i in self.patient_indices
                                    for k in self.linac_indices))
        self.model.minimize(total_wait + total_overdue)

    def setup_constraints(self):
        for i in self.patient_indices:
            # assignment contraints
            self.model.add_constraint(1 == self.model.sum(self.model.x[t,i,k]  for t in self.day_indices
                                                                for k in self.linac_indices), 'assignment_' + str(i))
            # ready day constraints
            if(self.STATIC_VERSION == True):
                first_valid_day = self.newPatients[i].releaseDay
            else:
                first_valid_day = max(self.newPatients[i].releaseDay, self.day_end)
            for t in range(self.day_begin, first_valid_day):
                for k in self.linac_indices:
                    self.model.add_constraint(0 == self.model.x[t,i,k], 'readyDay_' + str(i))

        # capacity contraints
        linac_occupancy = self.scenario.getOccupancyByDayAndLinacs()            # occ[t,k] occupancy at day t linac k
        linac_occupancy_palliative = self.scenario.getOccupancyOfPalliativeByDayAndLinacs()
        for t in self.day_indices:
            for k in self.linac_indices:
                avail_cap = self.scenario.single_linac_capacity - linac_occupancy[t, k]
                if(self.STATIC_VERSION == True):        #and t <= self.scenario.getNoSimDays()[1]
                    avail_cap_nonreserved = avail_cap
                else:
                    remaining_reserved = max(0, (1-self.reservation_rate) * self.scenario.single_linac_capacity - linac_occupancy_palliative[t,k])
                    avail_cap_nonreserved = max(0, avail_cap - remaining_reserved)
                self.model.add_constraint(self.model.sum(self.model.x[tt, i, k] * self.newPatients[i].duration
                                        for i in self.patient_indices if not self.newPatients[i].isPalliative() #curative only
                                        for tt in range(max(self.day_begin, t - self.newPatients[i].noSections + 1), t+1))
                                         <= avail_cap_nonreserved, 'capacity_res_' + str(t) + '_' + str(k))
    def print_information(self):
        # print("*************************** Result ***************************")
        self.model.print_information()
        self.model.report_kpis()

    def get_results(self) -> Scenario:
        '''return an rtsp_solution'''
        for i in self.patient_indices:
            for t in self.day_indices:
                for k in self.linac_indices:
                    if self.model.x[t,i,k].solution_value >= 0.99:
                        self.scenario.schedulePatient(self.newPatients[i], t, k, self.newPatients[i].noSections)

        solve_details = self.model.solve_details
        self.result_time = solve_details.time
        self.result_obj = self.model.solution.get_objective_value()
        self.result_gap = solve_details.gap
        self.result_sol = self.scenario
        return self.scenario

    @staticmethod
    def build_model(scenario: Scenario, lPatients: List[TPatient], day_start, day_end, conf, static = True,**kwargs):
        lpmodel = LPmodel(scenario, lPatients, day_start, day_end, conf, static, **kwargs)
        noNewPatients = lpmodel.setup_data()
        if(noNewPatients == 0):
            return None

        lpmodel.setup_variables()
        lpmodel.setup_constraints()
        lpmodel.setup_objective()
        
        return lpmodel

    def solve(self, **kwargs):
        sol = self.model.solve(log_output=MIP_LOG_OUTPUT, **kwargs)
        if sol is not None:
            if(MIP_LOG_OUTPUT == True):
                self.print_information()
            self.get_results()
            return self.result_sol
        else:
            print("* model is infeasible")
            return None