import logging
import os
import time

from RTSP.readwriteUtils import *
import RTSP.RTSP_utilities as rtsp_utils
import algorithm.simulation_MIP as sim_static
from RTSP import readwriteUtils as rw
from script_shap import _solve_ins
from config import Solver_Type

def runExpr(conf) -> 'TResult':
    '''run experiment for one instance
    :return TResult'''

    ins_path = conf.ins_path + '/' + conf.ins_name + '.csv'
    # sol_path = conf.solution_path + '/' + conf.ins_name + '.sol'
    logging.info(f'running exp - reading instance {ins_path}')
    scenario, lPatients = rw.read_instance_rtsp(ins_path)
    # logging.info(rtsp_utils.toStringInsInfor(scenario, lPatients))

    start = time.time()
    runresult = None
    mipgap = 1.0

    # solve the instance here
    # the algorithm has to take care of selecting patients in the simulation period only, as static has different strategy
    if(conf.solver in [Solver_Type.static]):     # MIP-based simulation
        solution, runresult, mipgap = sim_static.runExprStatic(scenario=scenario, lPatients = lPatients, conf=conf)

    elif(conf.solver in [Solver_Type.daily, Solver_Type.weekly]):
        solution, runresult, mipgap = sim_static.runExprPeriodic(scenario=scenario, lPatients=lPatients, conf=conf)

    # elif(conf.solver in [Solver_Type.greedy]):
    #     solution, runresult = greedy.runExpr(scenario=scenario, lPatients = lPatients, conf=conf)

    # elif(conf.solver in [Solver_Type.prediction_online, Solver_Type.daily_greedy]):
    else:
        solution, runresult = _solve_ins(scenario=scenario, lPatients = lPatients, conf=conf)
        

    run_time = time.time() - start
    result = rtsp_utils.ensembleResult(conf.ins_name, conf.ins_path, conf.solver, solution, runresult, run_time, mipgap, conf.simday)

    if(conf.solver in ['static']):
        os.makedirs(conf.solution_path, exist_ok = True)
        sol_path = conf.solution_path + '/' + conf.ins_name + '-' + conf.solver + '.sol'
        solution.saveSolToFile(output_path=sol_path)
        print('wrote solution to file ', sol_path)

    # save result
    if(conf.result_path != None):
        os.makedirs(conf.result_path, exist_ok = True)
        solver = conf.solver if conf.solver not in ['online_prediction'] else 'prediction'

        result_path = conf.result_path+ '/' + conf.ins_name + '-' + solver + '.out'
        result.save_result(result_path)
        print('wrote result to file ', result_path)
    print('time: ', run_time)

    return result


if __name__ == '__main__':
    conf = config.get_config()
  
    runExpr(conf)