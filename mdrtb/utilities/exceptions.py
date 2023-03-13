import functools
import requests

import logging

logger = logging.getLogger("django")


def handle_rest_exceptions(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.RequestException as request_err:
            logger.error(request_err, exc_info=True)
            raise Exception(
                "An error occured while processing your request. Please try again later"
            )
        except requests.exceptions.HTTPError as httperr:
            logger.error(httperr, exc_info=True)
            raise Exception(
                "An error occured while processing your request. Please try again later"
            )
        except requests.exceptions.ConnectionError as connection_err:
            logger.error(connection_err, exc_info=True)
            raise Exception("Please check your internet connection and try again")
        except Exception as e:
            raise Exception(e)

    return wrapper
