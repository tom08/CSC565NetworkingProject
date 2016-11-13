# Address of control server
SERVER_ADDR = "192.168.1.8"

# Directory where information on temp files is stored
SERVER_TEMP_INFO = "./server_file_info"

# File where information on temp files is stored
SERVER_TEMP_INFO_FILE = "temp_info.txt"

# Folder to hold temp files on server
SERVER_TEMP_FILES = "./temp_files"

# Directory on client where downloaded files will be placed
CLIENT_DOWNLOAD_DIR = "./downloads"

# Override settings with settings_local.py
try:
    from settings_local import *
except ImportError:
    pass
