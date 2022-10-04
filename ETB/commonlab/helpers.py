import requests
from django.http import JsonResponse



BASE_URL = 'http://46.20.206.173:18080/openmrs/ws/rest/v1/'



def getConceptsByType(req,type):
        url = BASE_URL + f'commonlab/concept?type={type}&lang=en'
        concepts = []
        headers = {'Authorization': f'Basic {req.session["encodedCredentials"]}' , 'Cookie' : f"JSESSIONID={req.session['sessionId']}"}
        print(headers)
        response = requests.get(url,headers=headers)
        if response.status_code == 200:
           for concept in response.json()['results']:
                concepts.append({'name' : concept['name'] , 'uuid' : concept['uuid']})
        else:
           print('FROM CONCEPT HELPER')
           print(response.status_code)
           print(response.json()['error']['message'])
        return concepts


def getAttributesByLabTest(uuid):
   url = BASE_URL + 'commonlab/labtestattributetype'
   params = {'testTypeUuid' : uuid,'v' : 'full'}
   response = requests.get(url=url,params=params)
   return response.json()['results']


def addOrEditTestType(req,data,url):
      headers = {'Authorization': f'Basic {req.session["encodedCredentials"]}' , 'Cookie' : f"JSESSIONID={req.session['sessionId']}"}
      print(data)
      response = requests.post(url,json=data,headers=headers)
      print(response.json())
      return response


def removeDuplicatesGroup(arr=[],grp=''):
      tCopy = arr.copy()
      tCopy.remove(tCopy[tCopy.index(grp)])
      return tCopy
   