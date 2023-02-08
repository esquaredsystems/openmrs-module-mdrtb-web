import re
from utilities import common_utils as u
from utilities import restapi_utils as ru
from django.core.cache import cache
from django.utils.safestring import SafeString as ss

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


def get_concept_from_cache(uuid):
    concepts = cache.get('concepts', [])
    concept = next((c for c in concepts if c['uuid'] == uuid), {})
    return bool(concept), concept


def get_concept(req, uuid):
    found, concept = get_concept_from_cache(uuid)
    if found:
        return concept
    try:
        status, response = ru.get(
            req, f'concept/{uuid}', {'v': "full", 'lang': req.session['locale']})
        if status:
            concepts = cache.get('concepts', [])
            concepts.append(response)
            cache.set('concepts', concepts, timeout=None)
            return response
    except Exception as e:
        print(e)
        raise Exception(str(e))


def get_location(uuid):
    pass


def get_user(req, username):
    status, response = ru.get(req, 'user', {'q': username, 'v': 'full'})
    if status:
        return response
    else:
        raise Exception('Cant find user')


def get_patient_identifier_types(req):
    status, response = ru.get(req, 'patientidentifiertype', {
                              'v': 'custom:(uuid,name)'})
    if status:
        return response['results']
    else:
        raise Exception('Cant find patient identifier types')


def get_global_properties(req, key):
    try:
        status, response = ru.get(req, 'systemsetting', {'q': key,
                                                         'v': 'custom:(value)'})
        if status:
            return response['results'][0]['value']
    except Exception as e:
        raise Exception(e)


def check_if_user_has_privilege(privilege_to_check, user_privileges):
    has_privilege = False
    for privilege in user_privileges:
        if privilege['display'] == privilege_to_check:
            has_privilege = True
    return has_privilege


def get_encounter_by_uuid(req, uuid):
    try:
        status, response = ru.get(req, f'encounter/{uuid}', {'v': 'full'})
        if status:
            return response
    except Exception as e:
        return None
