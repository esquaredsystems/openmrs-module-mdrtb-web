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
        return None
        
        



def calculate_age(dob):
    age = 0
    try:
        converted_date  = datetime.strptime(dob, '%Y-%m-%d').date()
        today_date= date.today()
        if today_date.month != converted_date.month:
            return (today_date.year-converted_date.year) - 1
        elif (today_date.day >= converted_date.day):
            return today_date.year-converted_date.year
    except Exception as e:
        return None
    


def iso_to_normal(date):
    try:
        normal = date[:date.find('T')].replace('-' , '.')
        return normal
    except Exception as e:
        return None




def remove_given_str_from_arr(arr=[], str=''):
    tCopy = arr.copy()
    try:
        tCopy.remove(tCopy[tCopy.index(str)])
        return tCopy
    except Exception as e:
        return arr


def remove_given_str_from_obj_arr(arr, str, call=None):
    temp = arr.copy()
    removedName = ''
    for item in temp:
        if item['value'] == str:
            removedName = item['name']
            temp.remove(temp[temp.index(item)])
    if call == 'commonlab':
        return removedName
    else:
        return temp

def remove_obj_from_objarr(obj,uuid_to_remove,key=None):
    for item in obj:
        if key:
            if item[key] == uuid_to_remove:
                obj.remove(item)
                return obj


