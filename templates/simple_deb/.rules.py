import os
from marek.input import get_input
from marek import project

data = {
   "deb_name": get_input("Debian package name", project.name.lower().replace(" ", "-").replace("_", "-")),
   "deb_maintainer": get_input("Debian maintainer", os.environ.get("DEBFULLNAME", None)),
   "deb_email": get_input("Debian email", os.environ.get("DEBEMAIL", None)),
   "deb_description": get_input("Debian description")
}
