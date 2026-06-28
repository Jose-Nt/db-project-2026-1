from dotenv import load_dotenv
import os


def setup_enviroment(
    ) -> None:
    """
    Setup the enviroment to execute the app locally with .env. 
    """
    env_path = os.path.join(os.getcwd(), "src", "config", ".env")
    load_dotenv(dotenv_path=env_path)