import os
from django.core.management.utils import get_random_secret_key
import utilities.common_utils as utils


def generate_production_envrionment_variables():
    mode = input("Are you building for production ? (Y/N) ")
    SECRET_KEY = get_random_secret_key()
    DEBUG = False
    REST_API_BASE_IP = "172.17.15.130:8080" if mode.upper() == 'Y' else "46.20.206.173:38080"
    with open(f"{utils.get_project_root()}/.env", 'w', encoding='utf-8') as env_file:
        env_file.write(f"SECRET_KEY={SECRET_KEY}")
        env_file.write("\n")
        env_file.write(f"DEBUG={DEBUG}")
        env_file.write("\n")
        env_file.write(f"REST_API_BASE_URL=http://{REST_API_BASE_IP}/openmrs/ws/rest/v1/")

    if not os.path.exists("logs"):
        os.makedirs("logs")


generate_production_envrionment_variables()
