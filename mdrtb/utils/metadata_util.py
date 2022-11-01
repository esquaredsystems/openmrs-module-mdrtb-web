from utils import util as u




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

    return value


def get_message_by_type(message_type,locale=None):
    messages = {}
    dir = f'{u.get_project_root()}/resources'
    if not locale:
        data = u.read_properties_file(f'{dir}/messages.properties' , 'r' , encoding='utf-8')
    else:
        data = u.read_properties_file(f'{dir}/messages_{locale}.properties' , 'r' , encoding='utf-8')
    if message_type:
        for message in data:
            split_msg = message.split('=')
            if split_msg[0].__contains__(message_type):
                messages[split_msg[0]] = split_msg[1]
    else:
        raise Exception("Please provide a valid message type")
    print(len(messages))
    return messages


print(get_message_by_type('tb03'))


def get_concept():
    # First lookup into cache

    # If found in cache, then return from cache

    # Otherwise make REST call
    pass


def get_locations():
    pass


def get_location(uuid):
    pass


def get_user():
    pass


def get_user(uuid):
    pass

