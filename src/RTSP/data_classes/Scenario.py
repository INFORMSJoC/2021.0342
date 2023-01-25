import numpy as np
import myUtils.myDateTime as mydatetime
from typing import List, Tuple, Dict
from RTSP.data_classes.TAppointment import TAppointment
from RTSP.data_classes.TPatient import TPatient


class Scenario:
    name: int
    noLinacs: int
    arrivalRate: int
    planningHorizon: int
    single_linac_capacity: int
    lAppointments: List[TAppointment]
    planningScope: int
    lPatients: List[TPatient]           # list of fixed patients only

    def __init__(self, name, noLinacs, capacity, _lambda, horizon, planningScope, listPatients, listAppointments):
        self.name = name
        self.noLinacs = noLinacs
        self.arrivalRate = _lambda
        self.planningHorizon = horizon
        self.single_linac_capacity = capacity
        self.planningScope = planningScope
        self.lPatients = listPatients   
        self.lAppointments = listAppointments  

        self._occupancy = np.zeros((self.planningScope, self.noLinacs))
        for app in self.lAppointments:
            self._occupancy[app.day, app.linac] += app.getAppDuration()

    @staticmethod
    def createSeedScenario(name, noLinacs, capacity, _lambda, horizon, planningScope):
        sce = Scenario(name, noLinacs, capacity, _lambda, horizon, planningScope,listPatients=[], listAppointments=[])
        for linac in range(0, noLinacs):
            for day in range(0, 50):
                sce._occupancy[day, linac] = 85 - day * (85/50)
        return sce

    def isPalliative(self, pIndex):
        return self.lPatients[pIndex].isPalliative()

    def schedulePatient(self, patient, startday, linac, noSections):

        endday = min(startday + noSections, self.planningScope - 1)
        for day in range(startday, endday):     #startday + noSections
            apptime = self.findFeasibleSlotForPatient(day, linac, patient.duration)
            assert apptime > -1
            endtime = apptime + patient.duration - 1
            
            self.lAppointments.append(TAppointment(day, linac, patient, apptime, endtime))
            self._occupancy[day, linac] = self._occupancy[day, linac] + patient.duration
        self.lPatients.append(patient)
        return self._occupancy

    def findFeasibleSlotForPatient(self, day, linac, duration) -> int:
        '''given a day and a linac, find the first feasible slot for a patient with a given duration
        :return a valid appointment time'''
        lApp = []
        for app in self.lAppointments:
            if(app.day == day and app.linac == linac):
                lApp.append(app)
        # sort app by
        lApp_sorted = sorted(lApp, key=lambda o:o.appointmenttime)
        noApp = len(lApp_sorted)
        if(noApp == 0):
            return 0
        for i in range(0, noApp-1):
            if(lApp_sorted[i].appointmentendtime + duration < lApp_sorted[i+1].appointmenttime):
                return lApp_sorted[i].appointmentendtime+1
        # the end of all appointment
        if(lApp_sorted[noApp-1].appointmentendtime + duration >= self.single_linac_capacity):
            print('ERROR - cant find an eligible slot for patient - day', day, 'linac', linac, 'duration', duration)
            for app in lApp_sorted:
                print(app)
            return -1
        else:
            return lApp_sorted[noApp-1].appointmentendtime+1

    def getSortedListAppointmentsOfPatient(self, pIndex)-> List[TAppointment]:
        lAss = [a for a in self.lAppointments if (a.patient.index == pIndex)]
        sortedLAss = sorted(lAss, key=lambda a:a.day)
        return sortedLAss

    def getStartDayOfPatient(self, pindex):
        lApps = self.getSortedListAppointmentsOfPatient(pindex)
        if(len(lApps) >0):
            return lApps[0].day
        return -1

    def getOccupancyByDay(self):
        '''return list of occupancy by day, from day 0 to planningScope'''
        occupancy = np.full(self.planningScope, 0)
        for app in self.lAppointments:
            occupancy[app.day] += app.getAppDuration()
        return occupancy

    def getOccupancyByDayAndLinacs(self):
        '''return list of occupancy by [day, linac]
        for debuging purposes '''
        occupancy = np.zeros((self.planningScope, self.noLinacs))
        for app in self.lAppointments:
            occupancy[app.day, app.linac] += app.getAppDuration()
        return occupancy

    def getOccupancyOfPalliativeByDayAndLinacs(self):
        '''return list of occupancy by [day, linac] for palliative patients only '''
        occupancy = np.zeros((self.planningScope, self.noLinacs))
        for app in self.lAppointments:
            if(app.patient.isPalliative()):
                occupancy[app.day, app.linac] += app.getAppDuration()
        return occupancy

    def getOccupancyAtBeginningOfTheDay(self, currentday: int):
        ''' get occupancy of linacs on the given day, take into account only patients admitted before currentday
        for generating training data
        it's expensive'''
        occupancy = np.full(self.planningScope, 0)
        for (i, p) in enumerate(self.lPatients):
            if (p.admissionDay < currentday):
                lApps = [a for a in self.lAppointments if (a.patient.index == p.index)]
                for a in lApps:
                    occupancy[a.day] = occupancy[a.day] + p.duration
        return occupancy
    
    def get_occ_beginning_day_and_pallitiave_of_the_day(self, currentday: int):
        ''' get occupancy of linacs on the given day, take into account only patients admitted before currentday
        and palliative patients admitted during the current day
        for generating training data for prediction-based batch scheduling
        it's expensive'''
        occupancy = np.full(self.planningScope, 0)
        for (i, p) in enumerate(self.lPatients):
            if (p.admissionDay < currentday) or (p.admissionDay == currentday and p.isPalliative()):
                lApps = [a for a in self.lAppointments if (a.patient.index == p.index)]
                for a in lApps:
                    occupancy[a.day] = occupancy[a.day] + p.duration
        return occupancy

    def getOccupancyRateByDay_AtBeginningOfAGivenDay_Statistics(self, _currentday, _noDays):
        '''get the occupancy rate of instances for a given number of days
        measure at the beginning of a given current day'''
        lOccupancy = self.getOccupancyByDay_ByPriority(_noDays)
        totalOccupancy = self.noLinacs * self.single_linac_capacity
        lOccupancyRate = []
        for i in range(0, 4):
            lOccupancyRate.append([])
            lOccupancyRate[i] = 100 * (lOccupancy[i]/totalOccupancy)
        return lOccupancyRate

    def getOccupancyRateByDay_ByPriority(self, _noDays):
        ''' return a dictionary with 5 keys, one for each priority, value is the list of occupancy by day'''
        lOccupancy = self.getOccupancyByDay_ByPriority(_noDays)
        totalOccupancy = self.noLinacs * self.single_linac_capacity
        lOccupancyRate = {}
        for i in range(0, 4):
            lOccupancyRate[i] = 100 * (lOccupancy[i]/totalOccupancy)

        overallOccupancy = [lOccupancyRate[0][i] + lOccupancyRate[1][i] + lOccupancyRate[2][i] + lOccupancyRate[3][i]
                        for i in range(0, _noDays)]
                        
        lOccupancyRate['overall'] = (overallOccupancy)
        return lOccupancyRate

    def getOccupancyByDay_ByPriority(self, _noDays: int):
        '''return 4 list of occupancy, one for each type of patient
        occupancy of linacs by day, for statistics methods
        includes also occupancy of fixed patients'''
        occupancy = []
        for i in range(0,4):
            occupancy.append([])
            occupancy[i] =  np.full(_noDays, 0) # 
        for app in self.lAppointments:
            if(app.day < _noDays):
                occupancy[app.patient.priority-1][app.day] += app.getAppDuration()
        return occupancy

    def getOccupancyByDay_Palliative(self, _noDays: int):
        '''return 4 list of occupancy, one for each type of patient
        occupancy of linacs by day, for statistics methods
        includes also occupancy of fixed patients'''

        lOccupancy = self.getOccupancyRateByDay_ByPriority(_noDays)  # 4 arrays, each for each type of patients
        occupancyPalliative = [lOccupancy[0][i] + lOccupancy[1][i] for i in range(0, _noDays)]
        return occupancyPalliative

    def getOccupancyByDay_Curative(self, _noDays: int):
        '''return 4 list of occupancy, one for each type of patient
        occupancy of linacs by day, for statistics methods
        includes also occupancy of fixed patients'''

        lOccupancy = self.getOccupancyRateByDay_ByPriority(_noDays)  # 4 arrays, each for each type of patients
        occupancyCurative = [lOccupancy[2][i] + lOccupancy[3][i] for i in range(0, _noDays)]
        return occupancyCurative

    def getListWaitDay(self, lPatients: List[TPatient]):
        '''return 5 arrays
                the first one is waiting time of all patients
                the next 4 ones are waiting time of patients by category'''
        lAllWaitDay = []
        for i in range(0, 5):
            lAllWaitDay.append([])

        for i, patient in enumerate(lPatients):
            startday = self.getStartDayOfPatient(patient.index)
            wait = mydatetime.getDistanceBetweenRelativeDays(patient.admissionDay, startday)
            lAllWaitDay[0].append(wait)

            if(wait <0):
                print(f'Scenrio p{patient.index} admission {patient.admissionDay} startday {startday} wait {wait}')

            for priority in range(1, 5):
                if lPatients[i].priority == priority:
                    lAllWaitDay[priority].append(wait)  # self._startdays[i] - patient['admissionDay']
        return lAllWaitDay

    def getListLateDay(self, lPatients: List[TPatient]):
        '''return 5 arrays
                the first one is overdue time of all patients
                the next 4 ones are overdue time of patients by category'''
        lAllLateDay = []
        for i in range(0, 5):
            lAllLateDay.append([])
        for i, patient in enumerate(lPatients):
            startday = self.getStartDayOfPatient(patient.index)
            late = mydatetime.getDistanceBetweenRelativeDays(patient.dueDay, startday) if(startday > patient.dueDay) else 0

            if(late <0):
                print(f'Scenrio p{patient.index} admission {patient.admissionDay} startday {startday} late {late}')

            lAllLateDay[0].append(late)
            for priority in range(1, 5):
                if lPatients[i].priority == priority:
                    lAllLateDay[priority].append(late)
        return lAllLateDay

    def getPatientById(self, pIndex) -> TPatient:
        lPatients = [p for p in self.lPatients if p.index == pIndex]
        if(len(lPatients) <= 0):
            return None
        else:
            return lPatients[0]

    def getListOfFixedPatients(self):
        '''return list of patient admitted at day -1'''
        lPatients = [p for p in self.lPatients if p.admissionDay <= -1]
        return lPatients

    def getListOfNewPatients(self):
        '''return list of patient admitted after day 0'''
        lPatients = [p for p in self.lPatients if p.admissionDay >= 0]
        return lPatients

    def get_patient_stats_by_day(self) -> Dict[int, Dict]:
        '''get number of patients of each day along with the total duration - used for prediction-based bath scheduling
        return a dictionary, key is admission date, value is a dictionary of priority'''
        l_stats_by_day = {}
        for p in self.lPatients:
            if(p.admissionDay not in l_stats_by_day.keys()):
                l_stats_by_day[p.admissionDay] = {1:[0,0], 2:[0,0], 3:[0,0], 4:[0,0]}           # each key is a tuple (no_patients, total_duration)
            l_stats_by_day[p.admissionDay][p.priority][0] += 1                          # number of patients
            l_stats_by_day[p.admissionDay][p.priority][1] += p.duration                 # total duration              

        return l_stats_by_day

    def getNoSimDays(self) -> Tuple[int, int]:
        '''return the first and last admission days'''
        if (len(self.lPatients) == 0):
            return (-1, -1)
        lDays = [p.admissionDay for p in self.lPatients]
        _min = min(lDays)
        _max = max(lDays)
        return (_min, _max)

    def printScenario(self):
        lFixedPatients = self.getListOfFixedPatients()
        print('{} linacs, {} horizon, {} patients, {} appointments'.format(self.noLinacs,
                                                                           self.planningHorizon, len(lFixedPatients), len(self.lAppointments)))
        dayindices = range(-1, max([p.admissionDay for p in self.lPatients]) + 1)      # simulation days
        lPatientsByDay = [[] for day in dayindices] 
        # -1 for fixed patients
        s = []
        for (i,p) in enumerate(self.lPatients):
            startday = self.getStartDayOfPatient(p.index)
            lPatientsByDay[p.admissionDay + 1].append('{}-d{}-s{}'.format(str(p.index), p.dueDay, startday))
        for day in dayindices:
            s.append('day{}: '.format(day) + '\t'.join(lPatientsByDay[day+1]))
        print('\n'.join(s))


    def saveSolToFile(self, output_path: str):
        '''save assignments of new patients to a solution file
        old format - temporary to stay compatible with the old version'''
        days = []
        linacs = []
        patients = []
        lPatients = self.getListOfNewPatients()
        for p in lPatients:         # so, new patients in ori_ins but not in solution
            lApps = self.getSortedListAppointmentsOfPatient(p.index)
            for a in lApps:
                days.append(a.day)
                linacs.append(a.linac)
                patients.append(a.patient.index)
        results = np.array(list(zip(days, linacs, patients)))

        np.savetxt(output_path, results, delimiter=',', fmt=['%s','%s','%s'], header="day,linac,patient")

    def check_sce_integrity(self, verbal: bool = True) -> bool:
        feasibility = True
        nodays = self.planningScope

        noAllPatients = len(self.lPatients)
        dict_count_sections = {}                 #a dictionary, key is pIndex and value is nb of sections of the corresponding patient
        dict_recal_startday = {}                # np.full(noAllPatients, -1)
        recal_occupancy = self.getOccupancyByDayAndLinacs()

        for ass in self.lAppointments:
            pIndex = ass.patient.index
            if pIndex in dict_count_sections:
                dict_count_sections[pIndex] = dict_count_sections[pIndex] + 1
                if(ass.day < dict_recal_startday[pIndex]):
                    dict_recal_startday[pIndex] = ass.day
            else:
                dict_count_sections[pIndex] = 1
                dict_recal_startday[pIndex] = ass.day

        # now, check start day and nb of section
        for i, p in enumerate(self.lPatients):
            startday = self.getStartDayOfPatient(p.index)
            if(dict_recal_startday[p.index] != startday):
                if(verbal == True):
                    print('~fail start day calculating p', p, ' d', startday)
                feasibility = False
            if(dict_recal_startday[p.index] == -1):
                if (verbal == True):
                    print('~fail p', p, ' startday=-1')
                feasibility = False
            if(dict_count_sections[p.index] != p.noSections):
                if (verbal == True):
                    print('~fail p', p, ' nosection =', dict_count_sections[p.index], ' not sufficient ', p.noSections)
                feasibility = False

        # check occupancy
        for day in range(0, nodays):
            for linac in range(0, self.noLinacs):
                if(recal_occupancy[day, linac] != self._occupancy[day, linac]):
                    if (verbal == True):
                        print('~fail occupancy consistency d', day, ' k', linac, ' is ', recal_occupancy[day, linac], 'recorded',self._occupancy[day, linac])
                    feasibility = False
                if(self._occupancy[day, linac] > self.single_linac_capacity):
                    if (verbal == True):
                        print('~capacity violated, day ', day, ' linac ', linac,
                          ' occupancy = ', self._occupancy[day, linac], ' over capacity ', self.single_linac_capacity)
                    feasibility = False

        if(feasibility == True and verbal == True):
            print('solution is valid')
        return feasibility