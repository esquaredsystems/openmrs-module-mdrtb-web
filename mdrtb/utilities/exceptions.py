import functools
import requests


def handle_rest_exceptions(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.HTTPError as httperr:
            raise Exception(
                "An error occured while processing your request. Please try again later"
            )
        except requests.exceptions.ConnectionError as connection_err:
            raise Exception("Please check your internet connection and try again")
        except requests.exceptions.RequestException as err:
            raise Exception(
                "An error occured while processing your request. Please try again later"
            )

    return wrapper
