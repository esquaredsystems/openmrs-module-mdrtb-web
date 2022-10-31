from pathlib import Path






def get_project_root() -> Path:
    return Path(__file__).parent.parent


def removeGivenStrFromArr(arr=[], str=''):
    tCopy = arr.copy()
    tCopy.remove(tCopy[tCopy.index(str)])
    return tCopy


def removeGivenStrFromObjArr(arr, str, call):
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

