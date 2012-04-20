""" Marek: tool for creating various projects from templates. """

import sys
from imp import load_source
from argparse import ArgumentParser
from shutil import copytree, Error, rmtree
from os import listdir, rename, walk, remove
from os.path import expanduser, join, isdir, exists, abspath, basename, dirname

from marek import project


RULES_FILE = '.rules.py'
TEMPLATE_PATHS = [
    expanduser("~/.marek"),
    "/usr/share/marek"
]


def normalize(file_name):
    """
    @file_name(string): file name to normalize
    @returns: absolute file name (starts with /)
    """
    if file_name.startswith("~"):
        file_name = expanduser(file_name)
    elif file_name.startswith("/"):
        pass
    else:
        file_name =abspath(file_name)
    return file_name


def get_available_templates():
    """ @returns (dict): {"template_name": "/path/to/template_name"} """
    dirs = {}
    for tdir in reversed(TEMPLATE_PATHS):
        if not (tdir and exists(tdir)):
            continue
        for template in listdir(tdir):
            if template.startswith("."):
                continue
            template_dir = join(tdir.rstrip("/"), template)
            if not isdir(template_dir):
                continue
            dirs[template] = template_dir
    return dirs


def render_string_template(template, data):
    """ Default string template renderer """
    from string import Template
    class CustomTpl(Template):
        delimiter = "%"
    return CustomTpl(template).safe_substitute(**data)


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
            with open(old_name) as f:
                info = render(f.read(), data)
            new_name = render(old_name, data)
            if old_name != new_name:
                rename(old_name, new_name)
            with open(new_name, "w") as f:
                f.write(info)
    # no need to have the rules file
    remove(join(clone_path, RULES_FILE))
    # if it the rules say that only one file in the directory is important - skip everything else
    file_name = getattr(rules, "file_name", None)
    if file_name:
        file_path = os.path.join(clone_path, file_name)
        if os.path.exists(file_path):
            parent_dir = os.path.dirname(clone_path)
            new_name = os.path.join(parent_dir, file_name)
            rename(file_path, new_name)
            remove(clone_path)


def clean_and_exit(clone_path, msg):
    """ Removes the clone, prints message and exits """
    print msg
    rmtree(clone_path)
    sys.exit(1)


def process_template(template_name, clone_path, quiet=False, force=False):
    """ Tries to clone the template into a project located in the current directory """
    try:
        assert template_name
        assert clone_path
    except AssertionError:
        print "Please specify a source template and project location."
        sys.exit(1)
    clone_path = normalize(clone_path)
    parent_dir = dirname(clone_path)
    project_name = basename(clone_path)
    if not exists(parent_dir):
        print "Directory %s where project '%s' was supposed to be created does not exist" % (parent_dir, project_name)
        sys.exit(1)
    try:
        template_path = get_available_templates()[template_name]
        if exists(clone_path):
            if not force:
                choice = "null"
                while choice not in "ynYN":
                    choice = raw_input(
                        "Directory %s already exists. Do you want to override it (wipes everything)? [y/N]" % clone_path
                    )
                if choice and choice in "yY":
                    force = True
            if force:
                rmtree(clone_path)
                print "Directory %s already existed but was overriden." % clone_path
            else:
                print "Not overriding..."
                sys.exit(0)
        copytree(template_path, clone_path)
        process_clone(clone_path, load_rules(template_path, project_name, quiet))
    except KeyError:
        clean_and_exit(clone_path, "Template %s was not found" % template_name)
    except Error, e:
        clean_and_exit(clone_path, "Cloning error: %s" % e)
    except KeyboardInterrupt:
        clean_and_exit(clone_path, "\nInterrupted")


def show_templates(plain=False):
    """ Shows all available templates """
    templates = sorted(get_available_templates().keys())
    if plain:
        print " ".join(templates)
    else:
        print "Avaliable templates:"
        for template in templates:
            print template
    sys.exit(0)


def main():
    """ Entry point """
    parser = ArgumentParser()
    parser.add_argument('-q', '--quiet', action='store_true', help='Use default values without asking')
    parser.add_argument('-l', '--list', action='store_true', help='Show available templates')
    parser.add_argument('-f', '--force', action='store_true',
                        help='Override the directory if it already exists (removes it, not merges)')
    parser.add_argument('--list-plain', action='store_true', help='Show available templates as a one line string')
    parser.add_argument('template', nargs='?', default=None)
    parser.add_argument('project_name', nargs='?', default=None)

    opts = parser.parse_args()
    if opts.list:
        show_templates()
    elif opts.list_plain:
        show_templates(True)
    else:
        process_template(opts.template, opts.project_name, opts.quiet, opts.force)


if __name__ == "__main__":
    main()
