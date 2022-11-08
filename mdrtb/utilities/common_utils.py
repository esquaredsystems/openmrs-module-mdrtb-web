from pathlib import Path
from datetime import datetime , date





def get_project_root() -> Path:
    return Path(__file__).parent.parent



def read_properties_file(filepath,mode,encoding):
    configdata = []
    try:
        file = open(filepath,mode,encoding=encoding)
        for line in file.readlines():
            configdata.append(line)
        file.close()
        return configdata  
    except Exception as e:
        print(e)



def calculate_age(dob):
    age = 0
    converted_date  = datetime.strptime(dob, '%d/%m/%Y %H:%M:%S').strftime("%d-%m-%Y")
    today_date= date.today()
    return today_date.year-int(converted_date[6:])
    





def remove_given_str_from_arr(arr=[], str=''):
    tCopy = arr.copy()
    tCopy.remove(tCopy[tCopy.index(str)])
    return tCopy


def remove_given_str_from_obj_arr(arr, str, call):
    temp = arr.copy()
    removedName = ''
    for item in temp:
        if item['value'] == str:
            removedName = item['name']
            temp.remove(temp[temp.index(item)])
    if call == 'helpers':
        return removedName
    else:
        return temp

