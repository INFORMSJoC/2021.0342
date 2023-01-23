import config
import pandas as pd
from RTSP import readwriteUtils as rw
import myUtils.common as cm
from RTSP.data_classes.Scenario import Scenario, TPatient
from myUtils import utils as ut
from typing import List

def genTrainDataFromSolutions(folder_instances, 
                                folder_solution, 
                                file_traindata, 
                                file_testdata,
                                dfResults_static, 
                                noFiles,
                                mode: str,
                                nosimdays = 30):
    '''main file to generate training data in batch
    mode = online or offline'''
    lSolution = ut.getFileNamesInFolder(folder_solution, extension='sol')      # in common
    df_train = pd.DataFrame()
    df_test =  pd.DataFrame()
    ltestfile, ltrainfile = [], []
    for (i, fsol) in enumerate(lSolution):      # 0-static.sol
        if (i%10 == 0):
            print('genTrainDataFromSolutions', i, fsol)
        if(i >= noFiles):
            break
        finsfull = folder_instances + '/' + fsol.split('-')[0] + '.csv'
        fsolful = folder_solution+ '/' +  fsol + '.sol'

        sol = rw.createInsFromSolFile(finsfull, fsolful, no_sim_day=nosimdays)
        if(sol == None):
            continue
        insname = int(fsol.split('-')[0].split('_')[0])                # very clumsy code
        rows = dfResults_static.loc[dfResults_static['ins_name'] == insname]
        row = rows.loc[dfResults_static['solver'] == 'static']
        if(row.empty == True):
            continue
        if(row.iloc[0]['mipgap'] >= 0.15):                    #temp, to remove non-optimal solutions
            continue

        dfsol = genTrainningDataForOneSol_online(sol)

        if(row.iloc[0]['ins_name'] % 5 == 0):
            df_test = pd.concat([df_test, dfsol])
            ltestfile.append(fsol)
        else:
            df_train = pd.concat([df_train, dfsol])
            ltrainfile.append(fsol)

    df_train.to_csv(file_traindata, index=False)
    df_test.to_csv(file_testdata, index=False)
    print('\tdone printing training data to {}, {} train files, {} test files'.format(file_traindata, len(ltrainfile), len(ltestfile)))

def createATrainingExample_online(  
                            _scenario: Scenario, 
                            _patient: TPatient, 
                            _startday: int, 
                            _occupancy: List[int], 
                            _currentday: int):
    lData = [_scenario.name,
             (_startday - _currentday),
             _currentday,
             _scenario.arrivalRate,
             _scenario.single_linac_capacity * _scenario.noLinacs,
             _patient.priority,
             _patient.noSections,
             _patient.duration,
             (_patient.releaseDay - _currentday),
             (_patient.dueDay - _currentday)]
    capacity = _scenario.noLinacs * _scenario.single_linac_capacity
    for o in range(_currentday, _currentday + config.NO_DAYS_OCCUPANCY_INFOR):
        lData.append(capacity - _occupancy[o])
    return lData


def genTrainningDataForOneSol_online(sce: Scenario):
    '''truely online, recalculate occupancy everytime a new patient is admitted (not by the beginning of the day anymore)'''
    # initialize all features
    columns = ['instance', 'waitday', 'currentday', 'lambda', 'capacity',
               'priority', 'noSections', 'duration', 'readyday', 'dueday']
    for i in range(0, config.NO_DAYS_OCCUPANCY_INFOR):
        columns.append(str(i))

    lastsim = config.NO_DAYS_SIMULATION
    lAllData = []
    currentday = 0
    occupancy = sce.getOccupancyAtBeginningOfTheDay(currentday)
    for p in sce.lPatients:

        if (p.admissionDay > currentday):
            currentday = currentday + 1  # p['admissionDay']
            if (currentday > lastsim):
                break

        if(p.admissionDay == currentday):
            startday = sce.getStartDayOfPatient(p.index)

            if(p.isPalliative() == False):                         # only curative -> create a new training example for the given patient
                training_example = createATrainingExample_online(_scenario=sce, _patient= p, _startday=startday, _occupancy=occupancy, _currentday = currentday)
                lAllData.append(training_example)

            cm.updateOccupancy(occupancy, startday, p.noSections, p.duration)

    df = pd.DataFrame(lAllData, columns=columns)

    return df



