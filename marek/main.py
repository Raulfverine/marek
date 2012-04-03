""" Marek: tool for creating various projects from templates. """

import sys
from imp import load_source
from argparse import ArgumentParser
from shutil import copytree, Error, rmtree
from os import listdir, rename, walk
from os.path import expanduser, join, isdir, exists, abspath

from marek import project
from marek.input import NoValueError


RULES_FILE = '.rules.py'
TEMPLATE_PATHS = [
    "/usr/share/marek",
    expanduser("~/.marek")
]


def get_available_templates():
    """ @returns (dict): {"template_name": "/path/to/template_name"} """
    dirs = {}
    for tdir in reversed(TEMPLATE_PATHS):
        if not (tdir and exists(tdir)):
            continue
        for template in listdir(tdir):
            template_dir = join(tdir.rstrip("/"), template)
            if not isdir(template_dir):
                continue
            dirs[template] = template_dir
    return dirs


def render_string_template(template, data):
    """ Default string template renderer """
    from string import Template
    return Template(template).safe_substitute(**data)


def load_rules(template_path, project_name, quiet):
    """ Loads rules from the RULES_FILE """
    rules_file = join(template_path, RULES_FILE)
    if not exists(rules_file):
        return None
    project.name = project_name
    project.quiet = quiet
    return load_source('rules', rules_file)


def process_clone(clone_path, rules):
    """ Deals with cloned template """
    # init string processing function and template dict
    render = getattr(rules, "render", render_string_template)
    data = getattr(rules, "data", {})
    # process files and dirs
    for path, dirs, files in walk(clone_path):
        # process dirs
        for tdir in list(dirs):
            ndir = render(tdir, data)
            if tdir != ndir:
                rename(join(path, tdir), join(path, ndir))
                dirs.remove(tdir)
                dirs.append(ndir)
        # process files
        for tfile in files:
            old_name = join(path, tfile)
            with open(old_name, "r+") as f:
                info = render(f.read(), data)
                f.seek(0)
                f.write(info)
            new_name = render(old_name, data)
            if old_name != new_name:
                rename(old_name, new_name)


def clean_and_exit(clone_path, msg):
    """ Removes the clone, prints message and exits """
    print msg
    rmtree(clone_path)
    sys.exit(1)


def process_template(template_name, project_name, quiet=False):
    """ Tries to clone the template into a project located in the current directory """
    try:
        assert template_name
        assert project_name
        clone_path = abspath(project_name)
        template_path = get_available_templates()[template_name]
        copytree(template_path, clone_path)
        process_clone(clone_path, load_rules(template_path, project_name, quiet))
    except AssertionError:
        clean_and_exit(clone_path, "Please specify a source template and project name.")
    except KeyError:
        clean_and_exit(clone_path, "Template %s was not found" % template_name)
    except Error, e:
        clean_and_exit(clone_path, "Cloning error: %s" % e)
    except NoValueError, e:
        clean_and_exit(clone_path, "Value is missing and has no default value")
    except KeyboardInterrupt:
        clean_and_exit(clone_path, "\nInterrupted")


def show_templates():
    """ Shows all available templates """
    print "Avaliable templates:"
    for template in sorted(get_available_templates().keys()):
        print template
    sys.exit(0)


def main():
    """ Entry point """
    parser = ArgumentParser()
    parser.add_argument('-q', '--quiet', action='store_true', help='Use default values without asking')
    parser.add_argument('-l', '--list', action='store_true', help='Show available templates')
    parser.add_argument('template', nargs='?', default=None)
    parser.add_argument('project_name', nargs='?', default=None)

    opts = parser.parse_args()
    if opts.list:
        show_templates()
    else:
        process_template(opts.template, opts.project_name, opts.quiet)


if __name__ == "__main__":
    main()
