import time
from RTSP.readwriteUtils import *
import RTSP.RTSP_utilities as rtsp_utils
from algorithm.Solver_greedy_daily import Solver_greedy_daily
from algorithm.Solver_greedy_online import Solver_greedy_online
from myUtils import utils as ut
import regression.train_xgboost as trainxgboost
from algorithm.Solver_prediction_online import Solver_prediction_online
import algorithm.simulation_MIP as sim_static
import algorithm.construction_heuristic as greedy

import os

import pickle
import config
from config import Solver_Type
import xgboost as xgb
from RTSP.data_classes.TRunResult import TRunResult

def is_prediction_based_solver(solver_name: str):
    if(solver_name in [ Solver_Type.prediction_online]):
        return True
    return False

def load_model(modelfile: str, regression_mode):
    if (regression_mode == 'xgboost'):
        loaded_model = xgb.Booster()
        loaded_model.load_model(modelfile)
        return loaded_model
    else:
        loaded_model = pickle.load(open(modelfile, 'rb'))
        return loaded_model

def _solve_ins( scenario: Scenario, 
                        lPatients: List[TPatient], 
                        conf, 
                        loaded_model = None
            ) -> Tuple[Scenario, TRunResult]:
    '''run experiment greedy, daily greedy '''

    if(is_prediction_based_solver(conf.solver) == True):
        if(loaded_model == None):
            modelfile = config.get_modelfile(conf)
            loaded_model = load_model(modelfile, config.regression_mode)
            print('loaded model ', modelfile)

    lPatients_Selected = [p for p in lPatients if p.admissionDay < conf.simday]

    if (conf.solver == Solver_Type.greedy):
        solver = Solver_greedy_online(scenario, lPatients_Selected, loaded_model, conf.reservation_rate, regression_mode = None, config = conf)
    
    elif(conf.solver == Solver_Type.daily_greedy):
        solver = Solver_greedy_daily(scenario, lPatients_Selected, loaded_model, conf.reservation_rate, regression_mode = None, config = conf)

    elif (conf.solver == Solver_Type.prediction_online):                  # online prediction
        solver = Solver_prediction_online(scenario, lPatients_Selected, loaded_model, conf.reservation_rate_regression, regression_mode = conf.regression_mode, config = conf)
  
    else:           
        print(conf.solver, 'is not supported')
        return None

    sol = solver.solve()
    runresult = rtsp_utils.evaluateSolution(sol, lPatients_Selected, checkFeasibility=True, verbal=False)
    return (sol, runresult)

def solveOneInstance_multiple_algo(insname, result_folder, conf = None):
    '''solve an instance with many solver, write the result file and solution file'''
    ins_file = conf.base_folder + f'data/{insname}.csv'
    print('solving', ins_file)
    l_solver = [
                Solver_Type.greedy, 
                Solver_Type.daily_greedy,
                Solver_Type.prediction_online,
                Solver_Type.daily,
                Solver_Type.weekly,
                ]
    for solver in l_solver:
        print('solving ', solver)
        conf.solver = solver
        solfile = result_folder + f'/{insname}-' + conf.solver.value + '.sol'
        resultfile = result_folder + f'/{insname}-' + conf.solver.value + '.out'
        solveOneInstance(ins_file, resultfile, solfile, conf)
        print('done solving', solver, 'wrote results to ', resultfile)


def solveOneInstance(   insfile, 
                        resultfile, 
                        solfile = None, 
                        conf = None, 
                        loaded_model = None):

    if(conf == None):
        conf = config.get_config()
    scenario, lPatients = read_instance_rtsp(insfile)
    start = time.time()

    if(conf.solver in [Solver_Type.daily, Solver_Type.weekly]):
        sol, runresult, mipgap = sim_static.runExprPeriodic(scenario=scenario, lPatients=lPatients, conf=conf)

    elif(conf.solver in [Solver_Type.greedy]):
        sol, runresult = greedy.runExpr(scenario=scenario, lPatients = lPatients, conf=conf)

    else:
        sol, runresult = _solve_ins(scenario, lPatients, conf, loaded_model=loaded_model)

    run_time = time.time() - start
    result = rtsp_utils.ensembleResult(scenario.name, conf.ins_path, conf.solver, sol, runresult,
                                    run_time, _noSimDay=conf.simday)

    result.save_result(resultfile)
    if(solfile != None):
        sol.saveSolToFile(output_path=solfile)
        print('save solution file ', solfile)
    

def batch_simulation_single_solver(_config, instance_folder_path = None, output_path = None):
    '''solve all instances in the given folder with a single given solver'''
    if(instance_folder_path == None):
        instance_folder_path = _config.base_folder + 'data'
    if(output_path == None):
        output_path = _config.base_folder + 'output/results'

    loaded_model = None
    if(is_prediction_based_solver(_config.solver) == True):
        modelfile = config.get_modelfile(_config)
        print('loading model from ', modelfile)
        loaded_model = load_model(modelfile, _config.regression_mode)

    lFiles = ut.getFileNamesInFolder(instance_folder_path, extension='csv')
    for file in lFiles:
        if (int(file.split('_')[0]) % 5 == 0):
            print('solving {} ins {}'.format(_config.solver, file))
            insfile = instance_folder_path + '/' + file + '.csv'
            resultfile = output_path + '/' + file + '-' + _config.solver + '.out'
            solfile = output_path + f'/{file}-' + _config.solver.value + '.sol'
            
            solveOneInstance(insfile, resultfile, solfile=solfile, conf = _config, loaded_model = loaded_model)

def batch_simulation_all_alg():
    '''run batch simulation for all 5 algorithm'''    
    conf = config.get_config()
    lPolicies = [
                    Solver_Type.greedy,
                    Solver_Type.daily_greedy,
                    Solver_Type.daily,
                    Solver_Type.weekly, 
                    Solver_Type.prediction_online, 
                    ]
    for solver in lPolicies:
        conf.solver = solver
        batch_simulation_single_solver(conf)


if __name__ == '__main__':

    conf = config.get_config()
    os.makedirs(conf.result_path, exist_ok=True)

    trainxgboost.plot_shap_beeswarm(modelfile=conf.base_folder + '/output/prediction/xgboost.sav',
                            train_file=conf.base_folder + '/output/prediction/training_data.csv',
                            img_folder = f'{conf.result_path}')
