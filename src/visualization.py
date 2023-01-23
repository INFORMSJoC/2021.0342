import numpy as np
import matplotlib.pyplot as plt
from RTSP import readwriteUtils as rw
from config import Solver_Type
import config
from dataprocessor.result_processor import plotBoxPlotSimulation, processFolderResult
import csv
import os

def solution_plotWaitTime_single_instance(  
                                            ins_file, 
                                            sol_folder, 
                                            filename, 
                                            startday=0,
                                            simday=180, 
                                            result_file = None,
                                            file_img = None):

    lalg = ['greedy', 'daily_greedy', 'daily', Solver_Type.weekly.value, Solver_Type.prediction_online.value,'online_prediction_fluctuate']
    llabels = ['online-greedy', 'daily-greedy', 'daily-IP',  'weekly-IP', 'prediction', 'prediction*']

    lWaitDaysAll = [[],[],[],[],[]]          # for all, then P1 to P4
    lOverdueAll = [[],[],[],[],[]]           # for all, then P1 to P4
    s_wait = {}
    s_overdue = {}
    
    (ins, lpatients) = rw.read_instance_rtsp(ins_file)
    
    lPatients_Selected = [p for p in lpatients if p.admissionDay < simday and p.admissionDay >= startday]
    # print(f'read instance {len(lpatients)} patients {len(lPatients_Selected)} selected')

    d_results = {}
    for (i,alg) in enumerate(lalg):
        d_results[alg] = []
        fsolful = sol_folder + filename + '-' + alg + '.sol'
        sol = rw.createInsFromSolFile(ins_file, fsolful, no_sim_day=simday)
        lwaitdays = sol.getListWaitDay(lPatients_Selected) 
        loverdue = sol.getListLateDay(lPatients_Selected) 
        
        
        s_wait[alg] = ''
        s_overdue[alg] = ''
        for j in range(0, 5):
            lWaitDaysAll[j].append(lwaitdays[j])
            lOverdueAll[j].append(loverdue[j])
            d_results[alg].append(np.average(lwaitdays[j]))
            d_results[alg].append(np.average(loverdue[j]))

    # print(d_results)
    header = ['alg','wait (all)', 'late (all)', 'P1 wait', 'P1 late', 'P2 wait', 'P2 late','P3 wait', 'P3 late','P4 wait', 'P4 late',]
    with open(result_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for key, value in d_results.items():
            writer.writerow([key] + value)
        print('wrote summary of results to ', result_file)

    # # # to print box plot P1 -> P4
    # fig2, ax2 = plt.subplots(4, 2, figsize=(8, 8))  # sharex=True
    fig2, ax2 = plt.subplots(4, 2, figsize=(8, 8))  # sharex=True
    for j in range(0, 4):
        ax2[j, 0].boxplot(lWaitDaysAll[j + 1])
        ax2[j, 1].boxplot(lOverdueAll[j + 1])

    ax2[2, 0].set_ylabel('Waiting time (days)', fontsize=14) #labelpad=10
    ax2[2, 1].set_ylabel('Overdue time (days)', fontsize=14, labelpad=10) # labelpad=10
    for j in range(0, 3):
        plt.setp(ax2[j, 0].get_xticklabels(), visible=False)
        plt.setp(ax2[j, 1].get_xticklabels(), visible=False)
    ax2[3, 0].set_xticklabels(llabels,rotation=80,fontsize=13)
    ax2[3, 1].set_xticklabels(llabels,rotation=80,fontsize=13)

    plt.text(1.07, 0.5, 'P1', ha='center', va='center', transform=ax2[0, 1].transAxes, fontsize=15)
    plt.text(1.07, 0.5, 'P2', ha='center', va='center', transform=ax2[1, 1].transAxes, fontsize=15)
    plt.text(1.07, 0.5, 'P3', ha='center', va='center', transform=ax2[2, 1].transAxes, fontsize=15)
    plt.text(1.07, 0.5, 'P4', ha='center', va='center', transform=ax2[3, 1].transAxes, fontsize=15)
    # plt.subplots_adjust(left=0.086, right=0.94, top=0.97, bottom=0.11)
    plt.subplots_adjust(left=0.11, right=0.94, top=0.97, bottom=0.175, wspace=0.3)
    # plt.tight_layout()
    if(file_img != None):
        plt.savefig(file_img)
        print('printed to file ', file_img)
    else:
        plt.show()


def plot_results(base_folder, result_folder = None):
    '''process and plot results
    result_folder consists of .out files (results from different algorithms)'''
    os.makedirs(result_folder, exist_ok = True)

    folderResults = base_folder + '/output/results'
    fileCsvResults = result_folder + '/results.csv'
    print('folder results', folderResults)

    processFolderResult(folderResults, fileCsvResults)

    fig_file = f'{result_folder}/sim_results.png'
    plotBoxPlotSimulation(fileCsvResults, file_img=fig_file)
    print('saved figure to ', fig_file)


if __name__ == "__main__":
    conf = config.get_config()
    
    plot_results(base_folder = conf.ins_path, result_folder = conf.result_path)

    


