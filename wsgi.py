import os
import sys

# Agregar el directorio del proyecto al path de Python
path = os.path.dirname(__file__)
if path not in sys.path:
    sys.path.append(path)

# Importar la app de Flask
from app import app as application

# El objeto 'application' es el que PythonAnywhere busca por defecto
if __name__ == "__main__":
    application.run()
