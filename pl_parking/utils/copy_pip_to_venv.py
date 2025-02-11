import os
import shutil
import os
import shutil
import sys


def copy_pip(file_extension):
    
    script_path = os.path.dirname(__file__)
    venv_path = os.path.join(script_path, "..", "venv")
    pip_ini_path = os.path.abspath(os.path.join(script_path, f"pip.{file_extension}"))
    if not os.path.isfile(os.path.abspath(os.path.join(script_path, "..", "venv", f"pip.{file_extension}"))):
        shutil.copy(pip_ini_path, venv_path)
        if os.path.isfile(os.path.abspath(os.path.join(script_path, "..", "venv", f"pip.{file_extension}"))):
            print("Pip ini file copied to venv folder")
            print("Installing packages")
        else:
            print("Pip ini copying failed!r")

if __name__ == "__main__":
    file_extension = "ini"
    #if sys.platform.startswith('win'):
        # Code for Windows
        #$CODE_FOR_WINDOWS$
    if sys.platform.startswith('linux'):
        # Code for Linux/Ubuntu
        #$CODE_FOR_LINUX$
        file_extension = 'conf'
   
    copy_pip(file_extension)
