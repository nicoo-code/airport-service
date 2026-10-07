import os
import sys

# Agregar la raíz del servicio al sys.path
SERVICE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if SERVICE_ROOT not in sys.path:
    sys.path.insert(0, SERVICE_ROOT)
