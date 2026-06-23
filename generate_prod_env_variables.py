import os
from django.core.management.utils import get_random_secret_key
import utilities.common_utils as utils


def generate_production_envrionment_variables():
    with open(f"{utils.get_project_root()}/.env", "w", encoding="utf-8") as env_file:
        env_file.write(f"SECRET_KEY = {get_random_secret_key()}")
    if not os.path.exists("logs"):
        os.makedirs("logs")


generate_production_envrionment_variables()
