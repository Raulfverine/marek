import os
from marek.input import get_input
from marek import project
from marek.transformers import debianize, pythonize

data = {
   "deb_name": get_input("Debian package name", project.name, debianize),
   "python_name": get_input("Python package name", project.name, pythonize),
   "deb_maintainer": get_input("Debian maintainer", os.environ.get("DEBFULLNAME", None)),
   "deb_email": get_input("Debian email", os.environ.get("DEBEMAIL", None)),
   "deb_description": get_input("Debian description"),
   "gitignore": ".gitignore"
}
