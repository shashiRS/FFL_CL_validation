import os
import shutil


def copy_pip():

    script_path = os.path.dirname(__file__)
    venv_path = os.path.join(script_path, "..", "venv")
    pip_ini_path = os.path.abspath(os.path.join(script_path, "pip.ini"))
    if not os.path.isfile(os.path.abspath(os.path.join(script_path, "..", "venv", "pip.ini"))):
        shutil.copy(pip_ini_path, venv_path)
        if os.path.isfile(os.path.abspath(os.path.join(script_path, "..", "venv", "pip.ini"))):
            print("Pip ini file copied to venv folder")
        print("Installing packages")


if __name__ == "__main__":
    copy_pip()
