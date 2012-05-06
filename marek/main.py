""" Marek: tool for creating various projects from templates. """

import sys
import subprocess
import re
from imp import load_source
from argparse import ArgumentParser
from shutil import Error, rmtree
from os import listdir, rename, walk, remove, makedirs, readlink, symlink
from os.path import expanduser, join, isdir, exists, abspath, basename, dirname, islink

from jinja2 import Template

from marek import project


CHILD_TPL_FLAG = "marek-apprentice"
OVERRIDE_FLAG = "{[OVERRIDE]}"
RULES_FILE = 'rules.py'
PARENT_TPL_FILE = 'parent_tpl'
TEMPLATE_PATHS = [
    expanduser("~/.marek"),
    "/usr/share/marek"
]
IGNORE_PATTERNS = [
    "^.*\.pyc$" # all .pyc files
]


class CloneError(Exception):
    """ Error for cloning issues """
    pass


def remove_if_ignored(file_name):
    """ Removes file from the clone (not folder) if it is ignored """
    for pattern in IGNORE_PATTERNS:
        if re.match(pattern, file_name):
            remove(file_name)
            return True
    return False


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
        file_name = abspath(file_name)
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
    # pylint: disable=W0402, W0404, C0111, W0142
    return Template(template).render(**data)


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
    # pylint: disable=R0914
    # no need to have the rules file and the parent_tpl file
    remove(join(clone_path, RULES_FILE))
    remove(join(clone_path, PARENT_TPL_FILE))
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
            if remove_if_ignored(old_name):
                continue
            with open(old_name) as fil:
                info = render(fil.read(), data)
            new_name = render(old_name, data)
            if old_name != new_name:
                rename(old_name, new_name)
            with open(new_name, "w") as fil:
                fil.write(info)
    # if it the rules say that only one file in the directory is important - skip everything else
    file_name = getattr(rules, "file_name", None)
    if file_name:
        file_path = join(clone_path, file_name)
        if not exists(file_path):
            raise CloneError("File with name %s was not found in the clone" % file_name)
        parent_dir = dirname(clone_path)
        new_name = join(parent_dir, file_name)
        rename(file_path, new_name)
        rmtree(clone_path)
    # process postclone files
    for script in list(getattr(rules, "postclone_scripts", [])):
        script_path = join(clone_path, script)
        if not exists(script_path):
            raise CloneError("Script with name %s was not found in the clone" % file_name)
        subprocess.check_call("cd %s; . %s" % (clone_path, script_path), shell=True)
        remove(script_path)


def clean_and_exit(clone_path, msg):
    """ Removes the clone, prints message and exits """
    print msg
    rmtree(clone_path)
    sys.exit(1)


def process_file(src_file, dest_file):
    """
    Copies content of the src_file into dest_file. If dest_file was taken from the parent template and
    there is an {[EXTRA]} key, the key is replaced with content of src_file. Otherwise dest_file content
    is fully overriten.
    """
    # read data
    with open(src_file) as fil:
        new_data = fil.read()
    # generate a chain of templates
    parent_template = None
    current_template = dest_file
    cursor = 1
    if OVERRIDE_FLAG in new_data:
        new_data = new_data.replace(OVERRIDE_FLAG, "")
    else:
        while exists(current_template):
            parent_template = current_template
            current_template = "%s%s%d" % (dest_file, CHILD_TPL_FLAG, cursor)
            cursor += 1
    # write data
    with open(dest_file, "w") as fil:
        if parent_template:
            # in the chain of templates each has to extend one another
            new_data = "\n".join([
                "{%% extends '%s' %%}" % parent_template,
                new_data
            ])
        fil.write(new_data)


def copy_directory(source, dest):
    """ Copies the directory, ignores if it already exists """
    for path, dirs, files in walk(source):
        relative_src_path = path.replace(source, "").lstrip("/")
        abs_dest_path = join(dest, relative_src_path)
        if not exists(abs_dest_path):
            makedirs(abs_dest_path)
        for tdir in dirs:
            dest_dir = join(abs_dest_path, tdir)
            if not exists(dest_dir):
                makedirs(dest_dir)
        for tfile in files:
            src_file = join(path, tfile)
            dest_file = join(abs_dest_path, tfile)
            if islink(src_file):
                linkto = readlink(src_file)
                symlink(linkto, dest_file)
                continue
            else:
                process_file(src_file, dest_file)


def process_tpl_chain(tpl_name, dest):
    """ Copies a chain of parent -> child templates """
    if tpl_name not in get_available_templates():
        raise CloneError("Parent template %s was not found" % tpl_name)
    tpl_path = get_available_templates()[tpl_name]
    tpl_file = join(tpl_path, PARENT_TPL_FILE)
    if exists(tpl_file):
        with open(tpl_file) as fil:
            tpl_name = re.sub(r'[^\w-]', '', fil.read())
            process_tpl_chain(tpl_name, dest)
    copy_directory(tpl_path, dest)


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
        rules = load_rules(template_path, project_name, quiet)
        process_tpl_chain(template_name, clone_path)
        process_clone(clone_path, rules)
    except KeyError:
        clean_and_exit(clone_path, "Template %s was not found" % template_name)
    except Error, err:
        clean_and_exit(clone_path, "Cloning error: %s" % err)
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
