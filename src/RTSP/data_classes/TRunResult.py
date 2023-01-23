from typing import List, Optional, Any, Dict, Tuple
from dataclasses import dataclass, asdict
import json, jsons
import numpy as np

@dataclass
class TRunResult():

    feasibility: bool
    objval: float
    lWaitDayByPriority: List[int]  # all 5 numbers
    lLateDayByPriority: List[int]
    lAvgWaitDayByPriority: List[float]
    lAvgLateDayByPriority: List[float]
    avg_occupancy: Optional[float] = 0
    std_occupancy: Optional[float] = 0
    lOccupancy: Optional[Dict[Any, List[float]]] = None    
    lWaitAndOverdue: Optional[List[Tuple[int, int, int, int]]] = None       
    
    def __str__(self):
        s = ' totalwaitday: {} P1 {} P2 {} P3 {} P4 {}'.format(*self.lWaitDayByPriority)
        s += ' totallate: {} P1 {} P2 {} P3 {} P4 {}\n'.format(*self.lLateDayByPriority)
        savg = ' avgwaitday: {:.2f} P1 {:.2f} P2 {:.2f} P3 {:.2f} P4 {:.2f}'.format(*self.lAvgWaitDayByPriority)
        savg += ' avglate: {:.2f} P1 {:.2f} P2 {:.2f} P3 {:.2f} P4 {:.2f}\n'.format(*self.lAvgLateDayByPriority)
        return s + savg + ' feasibility: {}'.format(self.feasibility)

    def update_occupandy(self,_lOccupancy):
        self.lOccupancy = _lOccupancy
        self.avg_occupancy = np.average(self.lOccupancy['overall'])
        self.std_occupancy = np.std(self.lOccupancy['overall'])
    
    def filter_result_by_sim_day(self, start_simday, end_simday):

        if(self.lOccupancy != None):
            self.avg_occupancy = np.average(self.lOccupancy['overall'][start_simday:end_simday])
            self.std_occupancy = np.std(self.lOccupancy['overall'][start_simday:end_simday])
        else:
            self.avg_occupancy  = -1
            self.std_occupancy = -1

        if self.lWaitAndOverdue != None:
            lWait = {0:[], 1:[], 2:[], 3:[], 4:[]}              # 0 is overall, then P1 to P4
            lOverdue = {0:[], 1:[], 2:[], 3:[], 4:[]}
            for a in self.lWaitAndOverdue:
                if(a[0] >= start_simday and a[0] <= end_simday):            #if admission day is withing range
                    lWait[0].append(a[2])                   # overall
                    lOverdue[0].append(a[3])
                    lWait[a[1]].append(a[2])                # for each priority
                    lOverdue[a[1]].append(a[3])

            for pri in range(5):        # the first one is overall, then 4 priority
                self.lAvgWaitDayByPriority[pri] = np.average(lWait[pri])
                self.lAvgLateDayByPriority[pri] = np.average(lOverdue[pri])

    def as_dict(self):
        '''this is for saving the results to dataframe'''
        data = {}
        data['feasibility'] = self.feasibility
        data['objval'] = self.objval
        
        data['avg_occupancy'] = self.avg_occupancy
        data['std_occupancy'] = self.std_occupancy
        
        label_avgwait = ['avgwait','avgwaitP1','avgwaitP2','avgwaitP3','avgwaitP4']
        label_avglate = ['avglate','avglateP1','avglateP2','avglateP3','avglateP4']
        for (i, lb)  in enumerate(label_avgwait):
            data[lb] = self.lAvgWaitDayByPriority[i]
            data[label_avglate[i]] = self.lAvgLateDayByPriority[i]
       
        return data

@dataclass
class TResult():
    '''to store results of a single instance run'''
    ins_name: int
    ins_path: Optional[str]
    solver: Optional[str]

    simdays: int
    noLinacs: int
    arrivalrate: float
    noSlotsPerDay: int          # S
    planningHorizon: int
    lNoPatients: List[int]  
    lNoNewPatients: List[int]         # 5 numbers: all, P1, P2, P3, P4
    lNoSections: List[int]   # 5 numbers

    # run result
    runresult: TRunResult
    runtime: float
    mipgap: Optional[float]


    def save_result(self, _result_path: str) -> bool:
        with open(_result_path, 'w') as outfile:
            dumped = jsons.dump(self)
            json.dump(dumped, outfile, indent=4)
            return True
        
    @staticmethod
    def load_result_Jsons(_path: str) -> 'TResult':
        with open(_path) as json_file:
            dumped = json.load(json_file)
            result = jsons.load(dumped, TResult)
            result.ins_path = ''
            return result
        
    def as_dict(self):
        dict = asdict(self)
        dict['ins_name'] = int(dict['ins_name'])
        del dict['runresult']
        dict_runresult = self.runresult.as_dict()
        for (key, item) in dict_runresult.items():
            dict[key] = item
        return dict

    def toDictInsInforFromTResult(self):
        infor = {}
        scap = ['instance', 'simdays', 'P', 'lambda', 'noLinacs', 'S', 'T', 'Pnew',
                'P1', 'P2', 'P3', 'P4',
                'P1new', 'P2new', 'P3new', 'P4new', 'noSectionsP1', 'noSectionsP2', 'noSectionsP3', 'noSectionsP4',
                'feasibility', 'avgoccp', 'stdoccp']
        llabelwait = ['wait', 'waitP1', 'waitP2', 'waitP3', 'waitP4']
        llabellate = ['late', 'lateP1', 'lateP2', 'lateP3', 'lateP4']
        shortname = str(self.ins_name) #self.ins_name.split('_')[0]
        sinfor = [shortname, self.simdays, self.lNoPatients[0], self.arrivalrate, self.noLinacs,
                  self.noSlotsPerDay,
                  self.planningHorizon, self.lNoNewPatients[0],  # self._planningScope,
                  self.lNoPatients[1], self.lNoPatients[2], self.lNoPatients[3], self.lNoPatients[4],
                  self.lNoNewPatients[1], self.lNoNewPatients[2], self.lNoNewPatients[3],
                  self.lNoNewPatients[4],
                  self.lNoSections[1], self.lNoSections[2], self.lNoSections[3],
                  self.lNoSections[4],
                  self.runresult.feasibility, 
                  self.runresult.avg_occupancy,
                  self.runresult.std_occupancy]
        for (i, key) in enumerate(scap):
            infor[key] = sinfor[i]
        for i in range(0, 5):
            infor[llabelwait[i]] = self.runresult.lWaitDayByPriority[i]  # lwaitday_by_priority[i]
            infor[llabellate[i]] = self.runresult.lLateDayByPriority[i]  # llateday_by_priority[i]
        return infor