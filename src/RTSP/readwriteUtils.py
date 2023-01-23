import codecs

import config
from myUtils import myDateTime
from RTSP.data_classes.Scenario import TPatient, TAppointment, Scenario
from typing import List, Tuple

_all_priority = ["P1", "P2", "P3", "P4"]

def priority_to_number(pri):                    # convert priority as string to number (1 to 4)
    priority_map = {pri: i+1 for i, pri in enumerate(_all_priority)}
    return priority_map[pri.upper()]

class PatientPoolItem:
    def __init__(self, arr, time_granuality):

        self._patId = int(arr[0])
        self._treatmentID = '' # arr[1]
        self._treatmentPlan = ''
        self._urgency = arr[3]    # string
        self._noSections = int(arr[4])

        self._admissionDay = myDateTime.fromStringToDate(arr[5], "%Y-%m-%d %H:%M")    #  %H:%M
        self._readyDay = myDateTime.fromStringToDate(arr[6], "%Y-%m-%d")
        self._dueDay = myDateTime.fromStringToDate(arr[7], "%Y-%m-%d")
        self._duration = int(int(arr[8])/time_granuality)
        self._minTW = 0 
        self._maxTW = 120 

        if(self._urgency == ''):
            self._urgency='P3'


    @staticmethod
    def initializeFromCSVString(s: str, time_granuality: int):

        arr = [x.strip().strip('"') for x in s.split(',')]
        tm = PatientPoolItem(arr, time_granuality)
        return tm

    def parseToTPatient(self, index: int = -1) -> TPatient:

        priority = priority_to_number(self._urgency)
        patient = TPatient.parsePatient(index, self._treatmentID, self._patId, self._treatmentPlan,
                             priority, self._noSections, -1, -1, -1,
                             self._duration,self._minTW, self._maxTW)
        return patient

def loadPatientPool(file_patientpool: str, time_granuality: int, sorted = True) -> List[PatientPoolItem]:
    '''load patientpool
    as the old patientpool file is not available anymore
    this function load patient pool from real data
    return list of patients sorted by admission days'''

    print('reading patient pool file ' + file_patientpool)
    f = codecs.open(file_patientpool, "r", encoding='utf-8')
    _lPatientPoolItems = []
    for (i, line) in enumerate(f.readlines()):
        # print(i, line)
        if (i > 0):  # the header
            tm = PatientPoolItem.initializeFromCSVString(line, time_granuality)
            _lPatientPoolItems.append(tm)
    f.close()
    print('loaded ', str(len(_lPatientPoolItems)) + ' patients from the patient pool')
    if(sorted == True):
        _lPatientPoolItems.sort(key= lambda x: x._admissionDay)        # sort treatments by admission date, then write it down to fileout
    return _lPatientPoolItems


def read_instance_rtsp(path) -> Tuple[Scenario, List[TPatient]]:
    '''read a file, return a scenario (consists of fixed patients and their appointments)
    and a list of new patients (those are not included in the scenario)'''
    file = codecs.open(path, "r", encoding='utf-8')
    lines = [ll.strip().replace(',',';') for ll in file]
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("Name"):
            name = line.split(';')[1].split('_')[0] # name;000_3.5
            #utils.getNumbersFromString(line.split(';')[1])[0]
        elif line.startswith("K"):
            noLinacs = int(line.split(';')[1])
        elif line.startswith("S"):
            capacity = int(line.split(';')[1])
        elif line.startswith("Lambda"):
            arrivalrate = float(line.split(';')[1])
        elif line.startswith("T"):
            horizon = int(line.split(';')[1])
        elif line.startswith("scope in days"):
            scope = int(line.split(';')[1])
        elif line.startswith("noSimulationDays"):
            noSimulationDays = int(line.split(';')[1])
        elif line.startswith("current day"):
            currentday = int(line.split(';')[1])
        elif line.startswith("no patients"):
            arr = line.split(';')
            nopatients = int(arr[1])
            # sumduration = int(arr[3])
        elif line.startswith("no new patients"):
            nonewpatients = int(line.split(';')[1])
        elif line.startswith('index;treatmentID;'):             # header for the patient section
            patients = [TPatient.parsePatient(*row.split(';')) for row in lines[i + 1:i + 1 + nopatients]]
            i = i + nopatients
        elif line.startswith('fixed appointment'):
            noappointments = int(line.split(';')[1])
        elif line.startswith('day;linac;'):           # header for existing appointment section
            lApps = [row.split(';') for row in lines[i + 1:i + 1 + noappointments]]
            appointments = [TAppointment(int(r[0]), int(r[1]), patients[int(r[2])], int(r[3]), int(r[4])) for r in lApps]
            i = i + noappointments
        i += 1
    file.close()

    # split patients into fixed patients and new arrival flow
    lFixedPatients = []
    lNewPatients = []
    for p in patients:
        if(p.admissionDay == -1):               # just temporary, potential bugs
            lFixedPatients.append(p)
        else:
            lNewPatients.append(p)
    scenario = Scenario(name, noLinacs, capacity, arrivalrate, horizon, scope, lFixedPatients, appointments)
    return scenario, lNewPatients

def write_instance_tsp(filepath, name, noLinacs, noSlot, arrivalrate, horizon, scopeinday, noSimDays,lPatients: List[TPatient], lAppointment):
    
    with open(filepath, 'w+') as f:
        f.write("\n".join([
            "{};{}".format(k, v)
            for k, v in (
                ("Name", name),
                ("K", noLinacs),
                ("S", noSlot),
                ("Lambda", arrivalrate),
                ("T", horizon),
                ("scope in days", scopeinday),
                ("noSimulationDays", noSimDays),
                ("current day", 0),
                ("no patients", len(lPatients))
            )
        ]))
        f.write("\n")
        f.write("index;treatmentID;patID;careplan;priority;noSections;admissionDay;releaseDay;dueDay;duration;TWMin;TWMax\n")
        f.write("\n".join([
            "{};{};{};{};{};{};{};{};{};{};{};{}".format(p.index, p.treatmentID, p.patID, p.careplan, p.priority,
                                                         p.noSections, p.admissionDay, p.releaseDay, p.dueDay,
                                                         p.duration, p.TWMin, p.TWMax)
            for p in lPatients]))
        f.write("\n")
        f.write("fixed appointment;" + str(len(lAppointment))+"\n")
        f.write("day;linac;patientid;appointmenttime;\n")
        f.write("\n".join([
            "{};{};{};{};{}".format(a.day, a.linac, a.patient.index, a.appointmenttime, a.appointmentendtime) for a in lAppointment
        ]))

def createInsFromSolFile(ins_path: str, sol_path: str, conf = None, no_sim_day: int = None) -> Scenario:
    '''read the (old) solution file and return a new instance (with included solution)
    used for generating training data - read from static solution
    it's very temporary, to use the old solution format from the previous verson
    sound freaking clumsy'''
    # start = time.time()
    scenario, lPatients = read_instance_rtsp(ins_path)
    noSimDay = config.NO_DAYS_SIMULATION
    if(no_sim_day != None):
        noSimDay = no_sim_day
    elif(conf != None):
        noSimDay = conf.simday
    
    file = codecs.open(sol_path, "r", encoding='utf-8')
    lines = [ll.strip().replace(',', ';') for ll in file]
    
    # day, linac, patient
    lAppointments = [[int(a) for a in row.split(';')] for row in lines[1:]] # list of (day, linac, patientid)

    if(len(lAppointments) == 0):
        print('error, empty solution file', sol_path)
        return None

    for patient in lPatients:
        if(patient.admissionDay >= noSimDay):
            continue
        
        lApps_of_patient = [app for app in lAppointments if app[2] == patient.index]
        if(len(lApps_of_patient) <= 0 and patient.admissionDay < noSimDay):
            print('error right here {} does not have an appointment'.format(patient))
        scenario.lPatients.append(patient)
        
        for (day, linac, patientid) in lApps_of_patient:
            apptime = scenario.findFeasibleSlotForPatient(day, linac, patient.duration)
            assert apptime > -1
            endtime = apptime + patient.duration - 1
            scenario.lAppointments.append(TAppointment(day, linac, patient, apptime, endtime))
            scenario._occupancy[day, linac] = scenario._occupancy[day, linac] + patient.duration

    return scenario
