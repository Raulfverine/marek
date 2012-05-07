import os
from marek.input import get_input
from marek import project
from marek.transformers import debianize, pythonize

data = {
   "python_name": get_input("Python package name", project.name, pythonize),
}

extend = True
