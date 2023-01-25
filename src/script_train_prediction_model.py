
from RTSP.readwriteUtils import *

import dataprocessor.result_processor as resultprocessor
import regression.generate_traindata as datagenerator
import regression.train_model as trainmodel
import regression.train_xgboost as trainxgboost

import config
from config import Solver_Type
import os


def train_prediction_model( conf, 
                            model_file,
                            generate_train_data: bool = False, 
                            only_xgboost = False,
                            ):

    folderResults = conf.base_folder + '/output/results'
    fileCsvResults = conf.base_folder + '/output/results.csv'
    ins_folder = conf.base_folder + '/data'
    sol_folder = conf.base_folder + '/output/solutions_static'
    train_file, test_file = config.getRegressionTrainingFiles(conf)

    if(generate_train_data):

        dfResults = resultprocessor.processFolderResult(folderResults, fileCsvResults, start_simday=0, end_simday=30)
        mode = 'online' if conf.solver == Solver_Type.prediction_online else 'daily'

        datagenerator.genTrainDataFromSolutions(ins_folder, sol_folder,train_file, test_file, dfResults, noFiles=1000, mode = mode)

    if(only_xgboost == False):
        lregression_mode = ['MLP','SGD','Lasso','ElasticNet','DecisionTree','RandomForest'] 
        for mode in lregression_mode: 
            trainmodel.train_model(train_file, test_file, '', mode, save_model=False)

    trainxgboost.train_model_without_hypertunning(  
        train_file, 
        test_file, 
        modelfile = model_file, 
        )


if __name__ == '__main__':

    conf = config.get_config()
    conf.solver = Solver_Type.prediction_online
    # base_folder = ./data/4linacs/lambda5.0

    model_file = f'{conf.base_folder}/output/prediction/xgboost.sav'

    train_prediction_model(conf,
                            model_file=model_file,
                            only_xgboost=False
                            )
