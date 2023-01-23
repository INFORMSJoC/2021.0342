import os


def priority_to_number(pri):                    # convert priority as string to number (1 to 4)
    _all_priority = ["P1", "P2", "P3", "P4"]
    priority_map = {pri: i+1 for i, pri in enumerate(_all_priority)}
    return priority_map[pri.upper()]

def getNumbersFromString(s):
    l = []
    s = s.replace('[', ' ')
    s = s.replace(']', ' ')
    s = s.replace(':', ' ')
    s = s.replace('_', ' ')
    s = s.replace(',', ' ')
    s = s.replace('=', ' ')
    for t in s.split():
        try:
            l.append(float(t))
        except ValueError:
            pass
    return l
def splitString(s):
    l = []
    s = s.replace(':', ' ')
    s = s.replace('_', ' ')
    s = s.replace('-', ' ')
    s = s.replace(';', ' ')
    s = s.replace(',', ' ')
    for t in s.split():
        l.append(t)
    return l

def splitStringByDel(s, de):
    l = []
    s = s.replace(de, ' ')
    for t in s.split():
        l.append(t)
    return l

def checkEmptyRow(df):
    # check if the dataframe df has NaN value
    is_NaN = df.isnull()
    row_has_NaN = is_NaN.any(axis=1)
    rows_with_NaN = df[row_has_NaN]
    print(rows_with_NaN)

def getFileNamesInFolder(folder, extension):
    # list files, without extenstion
    listfiles = []
    extension = '.' + extension
    for subdir, dirs, files in sorted(os.walk(folder)):
        for file in sorted(files):
            names = os.path.splitext(file)
            if(names[1] == extension):
                listfiles.append(names[0])
    return listfiles