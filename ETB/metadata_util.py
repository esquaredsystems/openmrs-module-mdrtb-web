import configparser


def get(resource, parameters, full=False):
    base_url = "http://46.20.206.173:18080/openmrs/ws/rest/v1/" + resource + "?" + parameters + "&v=" 
    if (full) :
        base_url += "&v=full"
    return None


def get_global_property(key, default=None):
    """
    Read value of property (key) from Openmrs global properties
    """
    try:
        value = None
    except Exception as ex:
        value = default
    return value


def get_message(message_code, locale=None, default=None):
    """
    Read message text in given locale
    """
    dir = 'C:/apache-tomcat-6/webapps/openmrs/WEB-INF'
    try:
        config = configparser.RawConfigParser()
        if not locale:
            config.read("{}/messages.properties".format(dir), encoding='utf-8')
        else:
            config.read("{}/messages_{}.properties".format(dir, locale), encoding='utf-8')
        value = config.get(message_code)
        if not value:
            if not locale:
                config.read("{}/module_messages.properties".format(dir), encoding='utf-8')
            else:
                config.read("{}/messages_{}.properties".format(dir, locale), encoding='utf-8')
        value = config.get(message_code)
    except Exception as ex:
        if default:
            value = default
        else:
            value = message_code
    return value


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

