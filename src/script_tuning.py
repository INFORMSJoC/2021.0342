from RTSP.readwriteUtils import *

import config
from config import Solver_Type

from script_shap import batch_simulation_single_solver

from dataprocessor.result_processor import plot_tuning_all_together
import os

def run_tuning_one_setting(conf, reservation_rate, data_folder):

    conf.reservation_rate = reservation_rate/100
    conf.reservation_rate_regression = reservation_rate/100

    l_solvers = [
                Solver_Type.greedy,
                Solver_Type.daily_greedy, 
                Solver_Type.prediction_online, 
                Solver_Type.daily, 
                Solver_Type.weekly
                ]

    for solver in l_solvers:
        conf.solver = solver
        result_path = conf.base_folder + 'tuning/' + str(reservation_rate) + '/'
        print('running batch simulation for solver ', solver.value, 'writing to', result_path)
        batch_simulation_single_solver(conf,instance_folder_path = data_folder, output_path = result_path)
        print('done running batch simulation for solver ', solver.value)

def run_tuning(conf, base_folder):
    '''base_folder = './data/4linacs/lambda6.0/' '''

    data_folder = base_folder + 'data/'
    model_file = f'{base_folder}output/prediction/xgboost.sav'    # xgboost_online_prediction.sav'
    conf.regression_model_file = model_file

    l_reservation_rate = [100, 95, 90, 85, 80]
    for rr in l_reservation_rate:
        run_tuning_one_setting(conf, reservation_rate=rr, data_folder = data_folder)


if __name__ == '__main__':   
    conf = config.get_config()
    # conf.base_folder = './data/4linacs/lambda6.0/'

    if(conf.rerun == 1):
        run_tuning(conf, base_folder=conf.base_folder)

    os.makedirs(conf.result_path, exist_ok=True)
    plot_tuning_all_together(   base_folder=conf.base_folder,
                                folder_result=conf.result_path)
    
