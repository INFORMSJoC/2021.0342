import config
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

pd.options.mode.chained_assignment = None


def plotPatientFlow_detailed(treatmentfile, startday, endday, avg: float = None, file_img: str = None):
    '''plot real patient flow'''
    df = pd.read_csv(treatmentfile)

    for value in ['DueDay', 'ReadyDay', 'AppCreate', 'FirstTreatment', 'LastTreatment']:        # ['AppDateTime', 'ReadyDay', 'AppCreate', 'DueDay']:
        df[value] = pd.to_datetime(df[value])
        df[value] = df[value].dt.date
    print(df['Priority'])

    mask = (df['AppCreate'] > startday) & (df['AppCreate'] <= endday)
    df_short = df.loc[mask]

    grouped = df_short.groupby(['AppCreate'])
    
    intervals = range(0, len(grouped.groups))
    # working_dates = np.busday_offset(startday, intervals, weekmask='1111100', holidays=HOLIDAYS, roll="forward").tolist()
    # l_dates = [date for date in grouped.groups.keys() if date in working_dates]
    l_dates = [date for date in grouped.groups.keys()]
    
    l_no_patients = [grouped.groups[date].size for date in l_dates]
    l_avg = []
    NO_DAYS_FOR_AVG = 10
    for (i, d) in enumerate(l_dates):
        begin = max(0, i-NO_DAYS_FOR_AVG-1)
        if(i < len(l_dates) - 1):
            avg = np.average(l_no_patients[begin:i+1])
        else:
            avg = np.average(l_no_patients[begin:])
        l_avg.append(avg)

    
    print(len(l_dates), 'dates - from ', l_dates[0], 'to', l_dates[len(l_dates) - 1])
    print(l_no_patients)
    # print(l_avg)
    print(f'min avg {min(l_avg)} max avg {max(l_avg)}')

    fig, ax = plt.subplots(2, figsize=(20, 10))
    mid = int(len(l_dates)/2)
    ax[0].plot(l_dates[0:mid], l_no_patients[0:mid], '-b', label='daily arrivals')
    ax[0].scatter(l_dates[0:mid], l_no_patients[0:mid])
    ax[0].plot(l_dates[0:mid], l_avg[0:mid],'-r', label = 'avg. arrivals in the last 10 days')
    ax[0].legend(loc="upper right")

    ax[1].plot(l_dates[mid+1:], l_no_patients[mid+1:], '-b', label='daily arrivals')
    ax[1].scatter(l_dates[mid+1:], l_no_patients[mid+1:])
    ax[1].plot(l_dates[mid+1:], l_avg[mid+1:],'-r', label = 'avg. arrivals in the last 10 days')
    
    # ax.set_xlabel('day')

    ax[0].set_ylabel('number of patients')
    ax[1].set_ylabel('number of patients')
    if(file_img != None):
        print('printed to file ', file_img)
        plt.savefig(file_img)
    else:
        plt.show()

    print('no days: ', len(grouped.groups))

def plotPatientFlow(treatmentfile, startday, endday, avg: float = None, file_img: str = None):
    '''plot real patient flow'''
    df = pd.read_csv(treatmentfile)

    for value in ['DueDay', 'ReadyDay', 'AppCreate', 'FirstTreatment', 'LastTreatment']:        # ['AppDateTime', 'ReadyDay', 'AppCreate', 'DueDay']:
        df[value] = pd.to_datetime(df[value])
        df[value] = df[value].dt.date
    # print(df['Priority'])

    mask = (df['AppCreate'] > startday) & (df['AppCreate'] <= endday)
    df_short = df.loc[mask]

    grouped = df_short.groupby(['AppCreate'])
    l_dates = [date for date in grouped.groups.keys()]
    
    l_no_patients = [grouped.groups[date].size for date in l_dates]
    l_avg = []
    NO_DAYS_FOR_AVG = 10
    for (i, d) in enumerate(l_dates):
        begin = max(0, i-NO_DAYS_FOR_AVG-1)
        if(i < len(l_dates) - 1):
            avg = np.average(l_no_patients[begin:i+1])
        else:
            avg = np.average(l_no_patients[begin:])
        l_avg.append(avg)

    fig, ax = plt.subplots(figsize=(10, 3))

    plt.plot(l_dates, l_no_patients, '-b', label='daily arrivals')
    plt.plot(l_dates, l_avg,'--r', label = 'avg. arrivals in the last 10 days')
    plt.subplots_adjust(left=0.05, right=0.97)
    plt.legend(loc="upper right")
    
    # ax.set_xlabel('day')

    ax.set_ylabel('number of patients')
    if(file_img != None):
        print('saved image to file ', file_img)
        plt.savefig(file_img)
    else:
        plt.show()

if __name__ == "__main__":
    conf = config.get_config()              # ./data/
    os.makedirs(conf.result_path, exist_ok=True)

    treatmentfile = f'{conf.base_folder}treatment_removedlinacs.csv'

    startday = pd.to_datetime("2018-05-15").date() 
    endday = pd.to_datetime("2019-06-15").date()   
    fig_file =f'{conf.result_path}real_patient_flow.png'

    # plotPatientFlow_detailed(treatmentfile, startday, endday, file_img=fig_file)
    plotPatientFlow(treatmentfile, startday, endday, file_img=fig_file)


