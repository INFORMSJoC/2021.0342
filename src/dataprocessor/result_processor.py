
from config import Solver_Type
import pandas as pd
import matplotlib.pyplot as plt
from myUtils import utils
from typing import List
from RTSP.data_classes.TRunResult import TResult

def readResultFolder(folder: str, file_ext: str = 'out') -> List[TResult]:
    '''read a folder of jsons file and return a list of result'''
    lfiles = utils.getFileNamesInFolder(folder, file_ext)
    lresult = []
    for file in lfiles:
        file_path = folder + '/' + file +'.' + file_ext
        try:
            result = TResult.load_result_Jsons(file_path)
            if (result.solver == None or result.solver == 'prediction'):
                result.solver = file.split('-')[1]
            lresult.append(result)
        except:
            continue
    return lresult

def processFolderResult(folderResults, fileCsvResults, start_simday = None, end_simday = None):
    '''read folder results and write down the summary to a csv file'''
    lResults = readResultFolder(folderResults, file_ext='out')

    if(start_simday != None):
        for item in lResults:
            item.runresult.filter_result_by_sim_day(start_simday, end_simday)

    df = pd.DataFrame(data=[item.as_dict() for item in lResults])
    df.to_csv(fileCsvResults, index=False)
    print('prossing results - save {} items to file {}'.format(len(lResults), fileCsvResults))

    return df

def filterTestInstances(df, lAlgs):
    '''return new dataframe with rows of test (and eligible) instances only'''

    lInstances = df['ins_name'].unique()
    
    lInstances_Index = [l for l in lInstances] 
    lTestInstances = [a for a in lInstances_Index if a%5 == 0]
    lInfeasible = []
    
    for (i, ins) in enumerate(lTestInstances):

        dfIns = df.loc[df['ins_name'] == ins]        # get all rows of that ins

        for alg in lAlgs:
            row = dfIns.loc[dfIns['solver'] == alg]
            if row.shape[0] == 0:
                lInfeasible.append(ins)
                break

    for ins in lInfeasible:
        lTestInstances.remove(ins)

    dftest = df.loc[df['ins_name'].isin(lTestInstances)]
    return dftest


def plotBoxPlotSimulation(fileresult, file_img = None):
    '''print box plot P1 to P4
    fileresult is the dataframe file thing'''
    lPolicies = [
                    'static', 
                     Solver_Type.greedy,
                    Solver_Type.daily_greedy.value,
                    Solver_Type.daily,
                    Solver_Type.weekly, 
                    Solver_Type.prediction_online.value, 
                    ]
    lPolicites_label=[  
                        'offline', 
                        'online-greedy', 
                        'daily-greedy',
                        'daily-IP', 
                        'weekly-IP', 
                        'prediction',
                                ]

    df_all = pd.read_csv(fileresult)
    df_all = df_all.replace(to_replace='prediction', value='online_prediction')
    # print('dfall',df_all)
    df = filterTestInstances(df_all, lPolicies)        #take out only test instances

    label_avgwait = ['avgwait','avgwaitP1','avgwaitP2','avgwaitP3','avgwaitP4']
    label_avglate = ['avglate','avglateP1','avglateP2','avglateP3','avglateP4']
    # print('df',df.head())
    # print(df.solver)
    df_grouped = df.groupby('solver')

    # df_grouped.size().plot(kind='bar')

    datawait = []
    datalate = []
    
    for j in range(0,5):            # P, P1, P2, P3, P4
        datawait.append([])
        datalate.append([])
        for policy in lPolicies:
            data = df_grouped.get_group(policy)
            datawait[j].append(data[label_avgwait[j]])
            datalate[j].append(data[label_avglate[j]])

    # # # to print box plot P1 -> P4
    fig2, ax2 = plt.subplots(4,2, figsize=(7, 8))   #sharex=True
    for j in range(0,4):
        ax2[j,0].boxplot(datawait[j+1])
        ax2[j,1].boxplot(datalate[j+1])
    ax2[1, 0].set_ylabel('Average waiting time per patient (days)', fontsize=13) #, labelpad=6)
    ax2[1, 1].set_ylabel('Average overdue time per patient (days)', fontsize=13)

    for j in range(0,3):
        plt.setp(ax2[j,0].get_xticklabels(), visible=False)
        plt.setp(ax2[j, 1].get_xticklabels(), visible=False)
    ax2[3, 0].set_xticklabels(lPolicites_label, rotation=80, fontsize=13)
    ax2[3, 1].set_xticklabels(lPolicites_label, rotation=80,fontsize=13)

    plt.text(1.07, 0.5, 'P1', ha='center', va='center', transform=ax2[0,1].transAxes, fontsize=15)
    plt.text(1.07, 0.5, 'P2', ha='center', va='center', transform=ax2[1,1].transAxes, fontsize=15)
    plt.text(1.07, 0.5, 'P3', ha='center', va='center', transform=ax2[2,1].transAxes, fontsize=15)
    plt.text(1.07, 0.5, 'P4', ha='center', va='center', transform=ax2[3,1].transAxes, fontsize=15)

    plt.subplots_adjust(left=0.10, right=0.94, top=0.97, bottom=0.205, wspace=0.3)  # 0.08 without labelpad - with 0.11
    # plt.subplots_adjust(left=0.10, right=0.94, top=0.97, bottom=0.175, wspace=0.3)  # 0.08 without labelpad - with 0.11
    # plt.show()
    if(file_img != None):
        plt.savefig(file_img)



def plot_tuning_all_together(base_folder, folder_result,  start_simday = None, end_simday = None):
    '''base_folder = ./data/4linacs/lambda6.0/'''
    base_folder = f'{base_folder}/tuning'
    l_reservation_rate = [80, 85, 90, 95, 100]
    
    label_avglate = ['avglate','avglateP1','avglateP2','avglateP3','avglateP4']
    
    lPolicies = ['greedy', Solver_Type.daily_greedy.value,'daily',  'weekly', Solver_Type.prediction_online.value,] 
    lPolicites_label=[  'online-greedy', 'daily-greedy','daily-IP', 'weekly-IP', 'prediction',]

    fig, ax = plt.subplots(4,5, figsize=(18, 10))   #sharex=True

    for (i, rr) in enumerate(l_reservation_rate):
        folderResults = f'{base_folder}/{str(rr)}'
        fileCsvResults = f'{folder_result}/results_{str(rr)}.csv'

        processFolderResult(folderResults, fileCsvResults,start_simday = start_simday, end_simday = end_simday)

        df = pd.read_csv(fileCsvResults)
        df_grouped = df.groupby('solver')
        datalate = []
        for j in range(0,5):            # P, P1, P2, P3, P4
            datalate.append([])
            for policy in lPolicies:
                data = df_grouped.get_group(policy)
                datalate[j].append(data[label_avglate[j]])
        
        for j in range(0,4):                # priority
            ax[j,i].boxplot(datalate[j+1])
    
    plt.text(0.5, 1.17, '0%', ha='center', va='center', transform=ax[0,0].transAxes, fontsize=15)
    plt.text(0.5, 1.17, '5%', ha='center', va='center', transform=ax[0,1].transAxes, fontsize=15)
    plt.text(0.5, 1.17, '10%', ha='center', va='center', transform=ax[0,2].transAxes, fontsize=15)
    plt.text(0.5, 1.17, '15%', ha='center', va='center', transform=ax[0,3].transAxes, fontsize=15)
    plt.text(0.5, 1.17, '20%', ha='center', va='center', transform=ax[0,4].transAxes, fontsize=15)


    plt.text(1.07, 0.5, 'P1', ha='center', va='center', transform=ax[0,4].transAxes, fontsize=15)
    plt.text(1.07, 0.5, 'P2', ha='center', va='center', transform=ax[1,4].transAxes, fontsize=15)
    plt.text(1.07, 0.5, 'P3', ha='center', va='center', transform=ax[2,4].transAxes, fontsize=15)
    plt.text(1.07, 0.5, 'P4', ha='center', va='center', transform=ax[3,4].transAxes, fontsize=15)

    ax[0, 0].set_ylim(-5, 80)
    ax[1, 0].set_ylim(-5, 80)
    for j in range(2, 4):
        ax[j, 0].set_ylim(20, 80)

    for i in range(0,5):
        # plt.setp(ax[3, i].get_xticklabels(), visible=False)
        ax[3, i].set_xticklabels(lPolicites_label, rotation=75, fontsize=13)

        ax[0, i].set_ylim(-5, 60)
        ax[1, i].set_ylim(-5, 45)
        ax[2, i].set_ylim(10, 50)
        ax[3, i].set_ylim(-5, 40)

    # plt.tight_layout()
    # ax[2, 0].ylabel('Average overdue time per patient (days)', fontsize=13)
    plt.text(-0.2, 0.7, 'Average overdue time per patient (days)', ha='center', va='center', transform=ax[2,0].transAxes, rotation=90, fontsize=13)
    plt.subplots_adjust(left=0.05, right=0.97, top=0.90, bottom=0.175)

    if(folder_result == None):
        plt.show()
    else:
        file_img = f'{folder_result}/tuning.png'
        print('printed to file ', file_img)
        plt.savefig(file_img)



