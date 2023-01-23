
from RTSP.readwriteUtils import *
import config
from config import Solver_Type
from script_shap import solveOneInstance
import os
from visualization import solution_plotWaitTime_single_instance


def solveRealIns(base_folder, ins_file, result_folder = None, conf = None):
    '''
    base_folder: ./data
    '''
    simDay = 180

    regression_model_file = f'{base_folder}/7linacs/lambda10.1/output/prediction/xgboost.sav' 
    regression_model_file_fluctuate = f'{base_folder}/7linacs/lambda10.1_fluctuate/output/prediction/xgboost.sav' 

    conf.regression_model_file = regression_model_file
    
    conf.simday = simDay
    l_solver = [
                Solver_Type.greedy, 
                Solver_Type.daily_greedy,
                Solver_Type.daily,
                Solver_Type.weekly,
                Solver_Type.prediction_online,
                ]
    
    conf.reservation_rate = 0.9
    conf.reservation_rate_regression = 0.9

    for solver in l_solver:
        print('solving ', solver)
        conf.solver = solver
        solfile = result_folder  + '/realins-' + conf.solver.value + '.sol'
        resultfile = result_folder  + '/realins-' + conf.solver.value + '.out'
        solveOneInstance(   ins_file, resultfile = resultfile, solfile = solfile, conf = conf)
        print('done solving', solver, 'wrote results to ', resultfile)

    # then solve the problem with prediction_online with fluctuating arrival rate
    conf.solver = solver
    conf.regression_model_file = regression_model_file_fluctuate
    solfile = result_folder  + '/realins-online_prediction_fluctuate.sol'
    resultfile = result_folder  + '/realins-online_prediction_fluctuate.out'
    solveOneInstance(   ins_file, resultfile = resultfile, solfile = solfile, conf = conf)
    print('done solving', solver, 'wrote results to ', resultfile)

if __name__ == '__main__':
    conf = config.get_config()
    data_dir = conf.ins_path        # ./data/7linacs/
    rerun = conf.rerun

    output_dir = conf.result_path   #  ./script/output/real_ins/
    os.makedirs(output_dir, exist_ok = True)

    _file_img = f'{conf.result_path}/real_ins.png'
    _file_result = f'{conf.result_path}/summary.csv'
    _ins_file = f'{data_dir}/real_ins/realins.csv'  

    _sol_folder = f'{conf.ins_path}/real_ins/results/'  
    
    if(rerun == 1):
        os.makedirs(_sol_folder, exist_ok = True)
        solveRealIns(base_folder = data_dir, ins_file = _ins_file, result_folder = _sol_folder, conf = conf)
    
    print('processing....', _ins_file)
    solution_plotWaitTime_single_instance(
                        ins_file = _ins_file,
                        sol_folder = _sol_folder, 
                        filename = 'realins', 
                        result_file=_file_result,
                        file_img=_file_img)