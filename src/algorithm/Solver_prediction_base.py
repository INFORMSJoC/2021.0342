from typing import List
import numpy as np
import xgboost as xgb
import config


class Solver_prediction_base:
    '''base class for solver'''
    def __init__(self, scenario: 'Scenario', lPatients: List['TPatient'], loaded_model, reservation_rate, regression_mode, config = None) -> None:
        self.regression_mode = regression_mode
        self.scenario = scenario
        self.lPatients = lPatients
        self.loaded_model = loaded_model
        self.reservation_rate = reservation_rate
        self.config = config
        pass

  
    def solve(self) -> 'Scenario':
        '''would have to be implemented by the concrete class'''
        return None
    
    
    def predict_waitTime_onlinescheduling(self, patient: 'TPatient', remaining_cap: List[int]):
    # 'index', 'treatmentID', 'patID', 'careplan', 'priority', 'noSections', 'admissionDay', 'releaseDay', 'dueDay', 'duration', 'TWMin', 'TWMax'
        currentday = patient.admissionDay
        data = []
        data.append(patient.noSections)
        data.append(patient.duration)
        data.append(patient.releaseDay - patient.admissionDay)
        data.append(patient.dueDay - patient.admissionDay)
        data = np.concatenate((data, remaining_cap[currentday:currentday + config.NO_DAYS_OCCUPANCY_INFOR]))  # I feel stupid -_-
        data = data.reshape(1, -1)

        if(self.regression_mode == 'xgboost'):
            dtest = xgb.DMatrix(data)
            predict_train = round(self.loaded_model.predict(dtest)[0], 0)
        else:
            predict_train = round(self.loaded_model.predict(data)[0], 0)             # wait day, not start day
        predicted = int(round(predict_train,0))

        return predicted