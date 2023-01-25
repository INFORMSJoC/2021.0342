import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import xgboost as xgb
import matplotlib.pylab as plt
# from sklearn.model_selection import RandomizedSearchCV, KFold
import time
import shap
from shap import Explanation

import config
from regression.preprocessing import splitDataTarget, correlation_matrix_heatmap

def update_one_param(gridsearch_params, listparams_tobetuned, params, dtrain, num_boost_round):
    '''         try parameters from gre
    :param gridsearch_params: a grid with all possible couple of values of params
    :param listparams_tobetuned: name of params to be tuned, right now limit to 2 at the same time
    :param params: keep all params of xgboost
    :param dtrain: data for training
    :return: no return, just update params from params
    '''
    min_rmse = float("Inf")
    best_params = None
    for param1, param2 in gridsearch_params:
        print("CV with {}={}, {}={}".format(listparams_tobetuned[0], param1, listparams_tobetuned[1], param2))
        # Update our parameters
        params[listparams_tobetuned[0]] = param1
        params[listparams_tobetuned[1]] = param2

        cv_results = xgb.cv(params=params, dtrain=dtrain, num_boost_round=num_boost_round, seed=42, nfold=10,
                            metrics={'rmse'}, early_stopping_rounds=10)  # Run CV

        mean_rmse = cv_results['test-rmse-mean'].min()              # Update best RMSE
        boost_rounds = cv_results['test-rmse-mean'].argmin()
        print("\tRMSE {} for {} rounds".format(mean_rmse, boost_rounds))
        if mean_rmse < min_rmse:
            min_rmse = mean_rmse
            best_params = (param1, param2)
    print("Best params: {}={}, {}={}, RMSE: {}".format(listparams_tobetuned[0], best_params[0], listparams_tobetuned[1],
                                                       best_params[1], min_rmse))
    params[listparams_tobetuned[0]] = best_params[0]                # update tuned results for listparams_tobetuned in params
    params[listparams_tobetuned[1]] = best_params[1]

def train_xgboost_model(training_datafile, testing_datafile, savemodels):
    ''' train model with xgboost train and cv'''
    otrain = pd.read_csv(training_datafile)  # ,delimiter='\t'
    X_train, y_train = splitDataTarget(otrain)
    otest = pd.read_csv(testing_datafile)
    X_test, y_test = splitDataTarget(otest)
    dtrain = xgb.DMatrix(X_train, label=y_train, enable_categorical=True)
    dtest = xgb.DMatrix(X_test, label=y_test,enable_categorical=True)

    params = {                      # Parameters that we are going to tune (exept objective)
        'max_depth': 6,'min_child_weight': 1, 'subsample': 1.0, 'colsample_bytree': 0.9, 'eta': .1,
        'eval_metric': 'rmse', 'objective': 'reg:squarederror' }
    num_boost_round = 999

    # tune max_depth and min_child_weight together
    # a list containing all the combinations max_depth/min_child_weight that we want to try
    listparams_tobetuned = ['max_depth', 'min_child_weight']
    gridsearch_params = [(max_depth, min_child_weight)
        for max_depth in range(6, 12)
        for min_child_weight in range(3, 9)     ]
    update_one_param(gridsearch_params, listparams_tobetuned, params, dtrain, num_boost_round)

    listparams_tobetuned = ['subsample', 'colsample_bytree']
    gridsearch_params = [(subsample, colsample)
        for subsample in [i / 10. for i in range(7, 11)]
        for colsample in [i / 10. for i in range(7, 11)]        ]
    update_one_param(gridsearch_params, listparams_tobetuned, params, dtrain, num_boost_round)

    best_model = xgb.train(params=params, dtrain=dtrain,num_boost_round=num_boost_round,evals=[(dtest, "Test")], early_stopping_rounds=10)
    print("Best RMSE: {:.2f} with {} rounds".format( best_model.best_score, best_model.best_iteration + 1))
    if savemodels == True:
        best_model.save_model(config.get_modelfile())
        print('saved model to ', config.get_modelfile())

    predict_train = best_model.predict(dtrain)
    error_train = mean_squared_error(y_train, predict_train)
    predict_test = best_model.predict(dtest)
    error_test = mean_squared_error(y_test, predict_test)
    print('accuracy_score on train dataset : {:.2f} \t test dataset {:.2f}'.format(error_train,error_test))

def train_model_without_hypertunning(training_datafile, testing_datafile, modelfile):
    otrain = pd.read_csv(training_datafile)  # ,delimiter='\t'
    X_train, y_train = splitDataTarget(otrain)
    otest = pd.read_csv(testing_datafile)
    X_test, y_test = splitDataTarget(otest)

    params = {
        'max_depth': 8, 'min_child_weight': 4, 'eta': .1,  'colsample_bytree': 1,
        'subsample': 1.0, 'colsample_bytree': 0.9,
        'eval_metric': 'rmse', 'objective': 'reg:squarederror',
    }
    num_boost_round = 99
    dtrain = xgb.DMatrix(X_train, label=y_train,  feature_names=X_train.columns)
    dtest = xgb.DMatrix(X_test, label=y_test,  feature_names=X_test.columns)

    start = time.time()
    model = xgb.train(params, dtrain=dtrain, num_boost_round=num_boost_round, evals=[(dtest, "Test")],
                      early_stopping_rounds=10, verbose_eval=0)
    run_time = time.time() - start
    print('\ttrainning for {} - time {:.2f} '.format(config.regression_mode, run_time))

    model.save_model(modelfile)
    print('\tfinished training, saved model to ', modelfile)

    predict_train = model.predict(dtrain)
    MSE_train = mean_squared_error(y_train, predict_train)
    MAE_train = mean_absolute_error(y_train, predict_train)
    R2_train = r2_score(y_train, predict_train)

    # dtest = xgb.DMatrix(X_test, label=y_test, enable_categorical=True, feature_names=X_test.columns)
    predict_test = model.predict(dtest)
    MSE_test = mean_squared_error(y_test, predict_test)
    MAE_test = mean_absolute_error(y_test, predict_test)
    R2_test = r2_score(y_test, predict_test)
    print('\t\ttrain dataset MSE {:.2f} , MAE {:.2f}, R2 {:.2f}'.format(MSE_train, MAE_train, R2_train))
    print('\t\ttest dataset MSE {:.2f} , MAE {:.2f}, R2 {:.2f}'.format(MSE_test, MAE_test, R2_test))


def plot_shap_beeswarm(modelfile, train_file, img_folder = None):
    loaded_model = xgb.Booster()
    loaded_model.load_model(modelfile)

    otrain = pd.read_csv(train_file)  # ,delimiter='\t'
    X_train, y_train = splitDataTarget(otrain)

    tree_explainer = shap.TreeExplainer(loaded_model)
    shap_values_tree = tree_explainer.shap_values(X_train)
    
    plt_shap = shap.summary_plot(shap_values_tree, #Use Shap values array            
                             features=X_train, # Use training set features
                             feature_names=X_train.columns, #Use column names
                             show=False, 
                             max_display=20,
                             plot_size=(14,6)) # Change plot size
    plt.gcf().axes[-1].set_aspect(100)
    plt.gcf().axes[-1].set_box_aspect(100)

    global_shap = img_folder + 'global_shap.png'           # beeswarm
    plt.tight_layout()
    plt.savefig(global_shap)
    print('saved figure to ', global_shap)
    plt.clf()
    
    sv = tree_explainer(X_train)
    exp = Explanation(values=sv.values, 
                  base_values=sv.base_values, 
                  data=X_train.values, 
                  feature_names=X_train.columns)
    l_indices = [100, 5000]#10, 100, 1000, 5000, 7000, 12000]
    for idx in l_indices:                       
        plt.figure(figsize=(6,6))
        waterfall = shap.plots.waterfall(exp[idx], max_display=14, show=True)
        waterfall = f'{img_folder}waterfall_{idx}.png'
        plt.tight_layout()
        plt.savefig(waterfall)
        plt.clf()
        print('saved figure to ', waterfall)



if __name__ == "__main__":
    '''train the model, given training data and test data'''

    correlation_matrix_heatmap(training_datafile= './data/7linacs_10.1/output/prediction/training_data.csv', # train_file, 
                                img_file='./script/output/heatmap.png')