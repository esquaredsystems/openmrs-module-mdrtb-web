import re
from utilities import common_utils as u
from utilities import restapi_utils as ru





# def get_global_property(key, default=None):
#     """
#     Read value of property (key) from Openmrs global properties
#     """
#     try:
#         value = None
#     except Exception as ex:
#         value = default
#     return value


def get_message(message_code,locale=None,default=None):
    value = ''
    dir = f'{u.get_project_root()}/resources'
    if not locale:
        data = u.read_properties_file(f'{dir}/messages.properties' , 'r' , encoding='utf-8')
    else:
        data = u.read_properties_file(f'{dir}/messages_{locale}.properties' , 'r' , encoding='utf-8')
    if message_code:
        for message in data:
            split_msg = message.split('=')
            if split_msg[0] == message_code:
                value = split_msg[1]
            elif default:
                value = default
    else:
        raise Exception("Please provide a valid message code")

    if len(value) < 1:
        value = message_code
    cleaner = re.compile('<.*?>')
    return re.sub(cleaner,' ',value.strip())




# def get_message_by_type(message_type,locale=None):
#     messages = {}
#     dir = f'{u.get_project_root()}/resources'
#     if not locale:
#         data = u.read_properties_file(f'{dir}/messages.properties' , 'r' , encoding='utf-8')
#     else:
#         data = u.read_properties_file(f'{dir}/messages_{locale}.properties' , 'r' , encoding='utf-8')
#     if message_type:
#         for message in data:
#             split_msg = message.split('=')
#             if split_msg[0].__contains__(message_type):
#                 messages[split_msg[0]] = split_msg[1]
#     else:
#         raise Exception("Please provide a valid message type")
#     return messages




def get_concept():
    # First lookup into cache

    # If found in cache, then return from cache

    # Otherwise make REST call
    pass


def get_locations():
    pass


def get_location(uuid):
    pass


def get_user(req,username):
    status , response = ru.get(req,'user',{'q' : username,'v' : 'full'})
    if status:
        return response
    else:
        raise Exception('Cant find user')




