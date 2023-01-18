import re
import os
from utilities import common_utils as u
from utilities import restapi_utils as ru
import django
from django.core.cache import cache
from django.utils.safestring import SafeString as ss
import os

# os.environ['DJANGO_SETTINGS_MODULE'] = 'mdrtb.settings'
# django.setup()


def get_global_msgs(message_code, locale=None, default=None, source=None):
    if message_code:
        value = ''
        dir = f'{u.get_project_root()}/resources'
        if source is None:
            if locale is None:
                file = f'{dir}/messages.properties'
            else:
                file = f'{dir}/messages_{locale}.properties'

        if source == 'OpenMRS':
            if locale is None:
                file = f"{dir}/openMRS_messages.properties"
            else:
                file = f"{dir}/openMRS_messages_{locale}.properties"

        if source == 'commonlab':
            if locale is None:
                file = f'{dir}/commonlab_messages.properties'
            else:
                file = f'{dir}/commonlab_messages_{locale}.properties'

        data = u.read_properties_file(file, 'r', encoding='utf-8')
        if data is not None:
            for message in data:
                split_msg = message.split('=')
                if split_msg[0].strip() == message_code.strip():
                    value = split_msg[1]
                elif default:
                    value = default
        else:
            value = message_code
        if len(value) < 1:
            value = message_code
        cleaner = re.compile('<.*?>')
        return re.sub(cleaner, ' ', value.strip())

    else:
        raise Exception("Please provide a valid message code")


def get_concepts_and_set_cache(req):
    concepts = cache.get('concepts')
    if concepts is None:
        status, response = ru.get(
            req, 'concept', {'v': 'full', 'limit': '100'})
        if status:
            try:
                cache.set('concepts', response['results'], 1000000)
                concepts = cache.get('concepts')
                return concepts
            except Exception as e:
                print(e)
        else:
            print(response)
    else:
        return concepts


def get_concept_by_uuid(uuid, req):
    if 'concepts' in cache:
        concepts = cache.get('concepts')
    else:
        concepts = get_concepts_and_set_cache(req)
    concept_found = False
    for concept in concepts:
        if concept['uuid'] == uuid:
            concept_found = True
            return True, concept
    if not concept_found:
        status, response = ru.get(
            req, f'concept/{uuid}', {'v': "full", 'lang': req.session['locale']})
        if status:
            return status, response
        else:
            return False, "cant find"


def get_locations():
    locations = [
        {
            "level": "country",
            "name": "Tajikistan",
            "children": [
                {
                    "level": "region",
                    "name": "Душанбе",
                    "children": [
                        {
                            "level": "district",
                            "name": "Сино",
                            "children": [
                                {
                                    "level": "facility",
                                    "name": "МСШ (01)"

                                },
                                {
                                    "level": "facility",
                                    "name": "МСШ 1 (95)"

                                },
                                {

                                    "level": "facility",
                                    "name": "МСШ 10 (60)"

                                },
                                {
                                    "level": "facility",
                                    "name": "МСШ 11 (11)"

                                },
                                {
                                    "level": "facility",
                                    "name": "МСШ 12 (12)"

                                },
                            ]
                        },
                        {
                            "level": "district",
                            "name": "Фирдавсӣ",
                            "children": [
                                {
                                    "level": "facility",
                                    "name": "МСШ (01)"

                                },
                                {
                                    "level": "facility",
                                    "name": "МСШ 1 (95)"

                                },
                                {

                                    "level": "facility",
                                    "name": "МСШ 10 (60)"

                                },
                                {
                                    "level": "facility",
                                    "name": "МСШ 11 (11)"

                                },
                                {
                                    "level": "facility",
                                    "name": "МСШ 12 (12)"

                                },
                            ]
                        },
                        {
                            "level": "district",
                            "name": "Исмоили Сомонӣ",
                            "children": [
                                {
                                    "level": "facility",
                                    "name": "МСШ (01)"

                                },
                                {
                                    "level": "facility",
                                    "name": "МСШ 1 (95)"

                                },
                                {

                                    "level": "facility",
                                    "name": "МСШ 10 (60)"

                                },
                                {
                                    "level": "facility",
                                    "name": "МСШ 11 (11)"

                                },
                                {
                                    "level": "facility",
                                    "name": "МСШ 12 (12)"

                                },
                            ]
                        },
                        {
                            "level": "district",
                            "name": "Шоҳмансур",
                            "children": [
                                {
                                    "level": "facility",
                                    "name": "МСШ (01)"

                                },
                                {
                                    "level": "facility",
                                    "name": "МСШ 1 (95)"

                                },
                                {

                                    "level": "facility",
                                    "name": "МСШ 10 (60)"

                                },
                                {
                                    "level": "facility",
                                    "name": "МСШ 11 (11)"

                                },
                                {
                                    "level": "facility",
                                    "name": "МСШ 12 (12)"

                                },
                            ]
                        }
                    ]

                }
            ]
        },
        {
            "level": "country",
            "name": "Other"
        }

    ]
    return locations


def get_location(uuid):
    pass


def get_user(req, username):
    status, response = ru.get(req, 'user', {'q': username, 'v': 'full'})
    if status:
        return response
    else:
        raise Exception('Cant find user')


def get_patient_identifier_types(req):
    status, response = ru.get(req, 'patientidentifierype', {
                              'v': 'custom:(uuid,name)'})
    if status:
        return response['results']
    else:
        raise Exception('Cant find patient identifier types')
