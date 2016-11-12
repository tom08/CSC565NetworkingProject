SERVER_ADDR = "192.168.1.8"

# Override settings with settings_local.py
try:
    from settings_local import *
except ImportError:
    pass
