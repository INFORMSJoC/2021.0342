# import config

import config
import random
import os

import matplotlib.pyplot as plt
from RTSP import readwriteUtils as rw
from data_generator import fillLinacs_withoutSpecificLinac
import myUtils.common as cm
from typing import List


def capacity_simulation(    
    patientpoolfile: str, 
    nolinacs: int, 
    l_arrival_rates: List[float],
    output_folder: str = None,
    timegranuality: int = 5):
    '''simulate a given a set of lambda and capacity, plot the result
    to test if an instance setting is reasonable (nb of linacs vs arrival rate)'''
    _linacs = nolinacs
    _lambda = l_arrival_rates
    _noSimulationDays = 350
    noSlot = 600/timegranuality

    seed = [100, 120, 13, 444, 12, 1, 53,354, 23, 43, 542, 3, 34, 57, 98, 120]
    patientpool = rw.loadPatientPool(patientpoolfile, timegranuality)

    _capacity = _linacs * noSlot
    result_nocap = []
    result_wcap = []            # with capacity constraint
    for i in range(0, len(_lambda)):
        random.seed(seed[i])
        random.shuffle(patientpool)

        lAdmissionDay_nocap, lStartDay_nocap, occupancy_nocap = fillLinacs_withoutSpecificLinac(
            patientpool,
            _lambda[i], 
            _capacity, 
            _noSimulationDays, 
            False,
            )
        lCount, lSum, lAverage_nocap = cm.groupSumValuesByWeek([x for x in range(0, len(occupancy_nocap))], occupancy_nocap)
        result_nocap.append([_lambda[i], _linacs, [100 * o/_capacity for o in lAverage_nocap]])  # occupancy

        lAdmissionDay_wcapacity, lStartDay_wcapacity, occupancy_wcapacity = fillLinacs_withoutSpecificLinac(
            patientpool, 
            _lambda[i], 
            _capacity, 
            _noSimulationDays, 
            True,
            )

        lWaitDays_wcapacity = lStartDay_wcapacity - lAdmissionDay_wcapacity
        lCount, lSum, lAverage_wcap = cm.groupSumValuesByWeek(lAdmissionDay_wcapacity, lWaitDays_wcapacity)
        result_wcap.append([_lambda[i], _linacs, lAverage_wcap])                        # average wait day

    # plot occupancy - no capacity
    fig, ax = plt.subplots(1, 2, figsize=(14, 3)) 
    lenplot = int(_noSimulationDays/5) 

    x = [i for i in range(0, lenplot)]
    l_colors = ['black', 'blue', 'green', 'red']
    l_patterns = ["solid", "dotted", "dashed", "dashdot"]

    for i in range(0, len(_lambda)):
        ax[0].plot(x, result_nocap[i][2][:lenplot], label=str(_lambda[i]),  color = l_colors[i], ls= l_patterns[i])

    ax[0].hlines(100, 0, lenplot, color='r', ls='--')
    ax[0].set(xlabel='week', ylabel = 'occupancy (%)')           #xlabel='week', turn xlabel off if 2-column article
    ax[0].set_title('(a) average linac occupancy by arrival rate' )

    weeks = [w for w in range(0, len(result_wcap[0][2]))]
    
    for i in range(0, len(_lambda)):
        ax[1].plot(weeks, result_wcap[i][2], label=str(_lambda[i]), color = l_colors[i], ls= l_patterns[i])

    ax[1].legend(title='arrival rate (#patients/day)', loc='upper left')
    ax[1].set(xlabel='week', ylabel='average wait time (in days)')
    ax[1].set_title('(b) average waiting time by arrival rate')

    # plt.subplots_adjust(left=0.1, right=0.96,  bottom=0.09, top=0.93)
    plt.tight_layout()
    if(output_folder):
        figure_file = f'{output_folder}/capacity_simulation_{nblinacs}.jpg'
        plt.savefig(figure_file)
        print('save file to ', figure_file)
    else:
        plt.show()


if __name__ == "__main__":
    conf = config.get_config()

    nblinacs = conf.nblinacs
    
    patientpoolfile = f'{conf.base_folder}/data/treatmentpool_clean.csv'
    output_folder = f'{conf.base_folder}/script/output/'
    os.makedirs(output_folder, exist_ok = True)
    
    d_lambda = {
        4: [5.0, 5.5, 6.0, 6.5],
        6: [7.0, 8.0, 9.0, 10.0],
        8: [10.0, 11.0, 12.0, 13.0]}
    
    capacity_simulation(    
        patientpoolfile, 
        nolinacs=nblinacs, 
        l_arrival_rates=d_lambda[nblinacs], 
        output_folder=output_folder,
        )