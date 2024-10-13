import sys
import os
import streamlit.web.cli as stcli
from dotenv import load_dotenv


def main():
    load_dotenv()
    script_path = os.path.join(os.path.dirname(__file__), "main.py")
    sys.argv = ["streamlit", "run", script_path, "--server.port", os.environ['PORT_WEBAPP']]
    stcli.main()


if __name__ == "__main__":
    main()