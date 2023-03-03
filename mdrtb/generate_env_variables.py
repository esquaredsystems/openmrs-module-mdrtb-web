import os
from django.core.management.utils import get_random_secret_key
import utilities.common_utils as utils


def generate_production_envrionment_variables():
    SECRET_KEY = get_random_secret_key()
    DEBUG = False
    with open(f"{utils.get_project_root()}/.env", 'w', encoding='utf-8') as env_file:
        env_file.write(f"SECRET_KEY={SECRET_KEY}")
        env_file.write("\n")
        env_file.write(f"DEBUG={DEBUG}")
        env_file.write("\n")


generate_production_envrionment_variables()
