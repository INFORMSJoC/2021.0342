import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

NO_DAYS_OCCUPANCY_INFOR = 50
pd.options.mode.chained_assignment = None           # to supress the warning when drop columns

def splitDataTarget(df):       

    lower_lim = df['0'].quantile(.02)  
    df_new = df[(df['0'] > lower_lim)]

    df_new.drop(columns=['capacity'], axis=1, inplace=True)
    target = df_new['waitday']
    df_new.drop(columns=['instance', 'priority', 'waitday', 'currentday', 'lambda'], axis=1, inplace=True)
    dict_rename = {}
    for i in range(50):
        dict_rename[str(i)] = 'c' + str(i)
    df_new.rename(columns=dict_rename, inplace=True)

    return df_new, target

def correlation_matrix_heatmap(training_datafile, img_file = None):
    '''plot the correlation matrix with heatmap
    for feature selection '''
    otrain = pd.read_csv(training_datafile)  # ,delimiter='\t'
    X_train, y_train = splitDataTarget(otrain)

    # drop some columns as there are too many features
    l_dropped_columns = []
    for i in range(1, 17):
        l_dropped_columns.append('c' + str(i * 3))
        l_dropped_columns.append('c' + str(i * 3 + 1))
    print('dropping', l_dropped_columns)
    X_train.drop(columns=l_dropped_columns, axis=1, inplace=True)

    corrmat = X_train.corr()

    top_corr_features = corrmat.index
    plt.figure(figsize=(20,12))
    # plt.yticks(rotation=0)
    
    g=sns.heatmap(X_train[top_corr_features].corr(),annot=True,cmap="RdYlGn")
    g.set_yticklabels(g.get_yticklabels(), rotation=0)
    if(img_file != None):
        plt.savefig(img_file)
        print('printed heatmap to ', img_file)
    else:
        plt.show()

