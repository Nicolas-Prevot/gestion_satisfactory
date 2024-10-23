import sys
import os
import streamlit.web.cli as stcli
from dotenv import load_dotenv


def main() -> None:
    """
    Main function to run the Streamlit application via command line.

    This function loads environment variables, sets up the script path and arguments
    for running the Streamlit app, and then starts the Streamlit CLI.

    Returns
    -------
    None

    """
    load_dotenv()
    script_path = os.path.join(os.path.dirname(__file__), "main.py")
    sys.argv = ["streamlit", "run", script_path, "--server.port", os.environ["PORT_WEBAPP"]]
    stcli.main()


if __name__ == "__main__":
    main()
