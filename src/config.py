import argparse
from enum import Enum
import os

regression_mode='xgboost'        

CONST_RESERVE_LINAC = 0.9  
CONST_RESERVE_LINAC_REGRESSION = 0.9 
NO_DAYS_OCCUPANCY_INFOR = 50         
NO_DAYS_SIMULATION = 150             


class Solver_Type(str, Enum):
    static = 'static'
    daily = 'daily'
    weekly= 'weekly' # those are MIP-based                                                 
    greedy = 'greedy'        # construction heuristic
    daily_greedy = 'daily_greedy'
    prediction_online = 'online_prediction'          # sim regression

def get_config():

    parser = argparse.ArgumentParser(description='Radiotherapy Scheduling Problem')
    parser.add_argument('--mode', default='test', type=str, choices=['test', 'server'])     # server if run on server (thread=1)
    parser.add_argument('--rerun', default=0, type=int, choices=[0,1])     # server if run on server (thread=1)
    parser.add_argument('--base_folder', default='', type=str)

    parser.add_argument('--solver', default='static', type=str, choices=[c.value for c in Solver_Type])
    parser.add_argument('--timeout', default=1800, type=int)                # in seconds
    parser.add_argument('--simday', default=NO_DAYS_SIMULATION, type=int)
    parser.add_argument('--ins_path', default=None, type=str)
    parser.add_argument('--ins_name', default=None, type=str)
    parser.add_argument('--save_solution', default=False, type=bool)
    parser.add_argument('--solution_path', default=None, type=str)    
    parser.add_argument('--result_path', default=None, type=str)      
    parser.add_argument('--reservation_rate', default=CONST_RESERVE_LINAC, type=float)
    parser.add_argument('--reservation_rate_regression', default=CONST_RESERVE_LINAC_REGRESSION, type=float)

    # arguments for prediction-based
    parser.add_argument('--regression_mode', default='xgboost', choices=['MLP', 'SGD','Lasso', 'ElasticNet', 'SVR',
                                                                 'RandomForest', 'DecisionTree', 'xgboost'], type=str)
    parser.add_argument('--regression_model_file', default=None, type=str)

    parser.add_argument('--nblinacs', default=4, type=int, choices=[4, 6, 7, 8])

    config = parser.parse_args()

    config_d = vars(config)   

    config_d['NO_THREADS'] = 1 if config.mode == 'server' else 2

    return config

def getRegressionTrainingFiles(_conf):
    d = _conf.base_folder + '/output/prediction'
    os.makedirs(d, exist_ok=True)

    training_datafile = _conf.base_folder + '/output/prediction/training_data.csv'
    testing_datafile = _conf.base_folder + '/output/prediction/testing_data.csv'
    return training_datafile, testing_datafile


def get_modelfile(_config):                 
    # xgboost or other regression model
    if(_config.regression_model_file == None):

        model_file = os.path.dirname(_config.ins_path) + '/output/prediction/' + _config.regression_mode  + '.sav'
        return model_file

    else:
        return _config.regression_model_file
