import os
from django.core.management.utils import get_random_secret_key
import utilities.common_utils as utils


def generate_production_environment_variables():
    root = utils.get_project_root()
    example_path = root / ".env-example"
    env_path = root / ".env"

    with open(example_path, "r", encoding="utf-8") as f:
        template = f.read()

    env_content = template.replace("your-secret-key-here", get_random_secret_key())

    with open(env_path, "w", encoding="utf-8") as f:
        f.write(env_content)

    if not os.path.exists("logs"):
        os.makedirs("logs")


generate_production_environment_variables()
