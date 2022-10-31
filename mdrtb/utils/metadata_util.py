import configobj
import util




# def get_global_property(key, default=None):
#     """
#     Read value of property (key) from Openmrs global properties
#     """
#     try:
#         value = None
#     except Exception as ex:
#         value = default
#     return value


def get_message(message_code, locale=None, default=None):
    dir = f'{util.get_project_root()}/resources'
    if locale:
        file = open(f'{dir}/messages_{locale}.properties' , 'r' , encoding='utf-8')
    else:
        file = open(f'{dir}/messages.properties', 'r', encoding='utf-8')
    if message_code:
        try:
            for message in file.readlines():
                split_message = message.split('=')
                if split_message[0] == message_code:
                    return split_message[1]
                elif default:
                    return default
                else:
                    raise Exception("Please provide a valid key")

        except Exception as e:
            print(e)




print(get_message('tb'))


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

