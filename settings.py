"""
Author:         Thomas Kroll
File:           settings.py
Description:
    This file holds the default settings for the project.
    To override any of the settings, create a file called:
    "settings_local.py" in the same directory and re-define
    any of the settings that you want.
    SERVER_ADDR MUST be re-defined for the program to work in
    the way it was anticipated to.
"""

# Address of control server
# This will need to be overridden for production.
SERVER_ADDR = "localhost"

# Time the server will wait for a destination client to respond.
TIMEOUT = 5

# Directory where information on temp files is stored
SERVER_TEMP_INFO = "./server_file_info"

# File where information on temp files is stored
SERVER_TEMP_INFO_FILE = "temp_info.txt"

# Folder to hold temp files on server
SERVER_TEMP_FILES = "./temp_files"

# Directory to store client information on server
SERVER_CLIENT_INFO_DIR = "./clients"

# File where client info is stored on the server
SERVER_CLIENT_INFO = "clients.txt"

# Directory on client where downloaded files will be placed
CLIENT_DOWNLOAD_DIR = "./downloads"

# Override settings with settings_local.py
try:
    from settings_local import *
except ImportError:
    pass
