import pandas as pd
from sklearn.linear_model import SGDRegressor
from sklearn import linear_model
from sklearn.linear_model import ElasticNet
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.tree import DecisionTreeClassifier
import xgboost as xgb
import time

import pickle
from regression import preprocessing


def train_model(train_datafile, test_datafile, modelfile, regression_mode, save_model: bool = False):
    '''train and write the trained model to modelfile'''
    otrain = pd.read_csv(train_datafile)  # ,delimiter='\t'
    data_train, target_train = preprocessing.splitDataTarget(otrain)

    if(regression_mode == 'SGD'):
        reg = make_pipeline(StandardScaler(), SGDRegressor(max_iter=10000, tol=1e-3))

    elif(regression_mode == 'RandomForest'):
        reg = RandomForestRegressor(n_estimators=100, random_state=20)

    elif (regression_mode == 'DecisionTree'):
        reg = DecisionTreeClassifier(max_depth =15, random_state = 42)

    elif (regression_mode == 'xgboost'):
        reg = xgb.XGBRegressor(objective='reg:linear', colsample_bytree=0.3, learning_rate=0.1,
                                  max_depth=10, alpha=10, n_estimators=100)

    elif(regression_mode == 'SVR'):
        reg = make_pipeline(StandardScaler(), SVR(C=1.0, epsilon=0.2))

    elif (regression_mode == 'ElasticNet'):
        reg = ElasticNet()

    elif (regression_mode == 'Lasso'):
        reg = linear_model.Lasso(alpha=0.1, max_iter=1000)

    elif (regression_mode == 'MLP'):
        reg = make_pipeline(StandardScaler(), MLPRegressor(hidden_layer_sizes=(5),
                            activation='tanh', solver='lbfgs',   # sgd, adam, lbfgs
                            random_state=1, max_iter=10000))               # 10.80 11.47
    else:       #default
        print('ERROR regression type -{}- is not supported'.format(regression_mode))
        return

    start = time.time()
    reg.fit(data_train, target_train)
    run_time = time.time() - start
    print('\ttrainning for {} - time {:.2f} '.format(regression_mode, run_time))

    predict_train = reg.predict(data_train)
    MSE_train = mean_squared_error(target_train, predict_train)
    MAE_train = mean_absolute_error(target_train, predict_train)
    R2_train = r2_score(target_train, predict_train)
    print('\t\ttrain dataset MSE {:.2f} , MAE {:.2f}, R2 {:.2f}'.format(MSE_train, MAE_train, R2_train))
    if(save_model == True):
        print('write to model file {}'.format(modelfile))
        pickle.dump(reg, open(modelfile, 'wb'))  # current model: SGDRegressor dataset: 1.34   dataset: 1.309

    # test
    ortest = pd.read_csv(test_datafile)
    data_test, target_test = preprocessing.splitDataTarget(ortest)
    predict_test = reg.predict(data_test)
    MSE_test = mean_squared_error(target_test, predict_test)
    MAE_test = mean_absolute_error(target_test, predict_test)
    R2_test = r2_score(target_test, predict_test)
    print('\t\ttest dataset MSE {:.2f} , MAE {:.2f}, R2 {:.2f}'.format(MSE_test, MAE_test, R2_test))


def predict(test_datafile, modelfile):
    ortest = pd.read_csv(test_datafile)
    data_test, target_test = preprocessing.splitDataTarget(ortest)
    reg = pickle.load(open(modelfile, 'rb'))
    predict_test = reg.predict(data_test)
    MSE_test = mean_squared_error(target_test, predict_test)
    MAE_test = mean_absolute_error(target_test, predict_test)
    print('test dataset MSE {:.2f} , MAE {:.2f}'.format(MSE_test, MAE_test))

