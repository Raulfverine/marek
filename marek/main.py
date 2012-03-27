""" Marek: tool for creating various projects from templates. """

import sys
from imp import load_source
from argparse import ArgumentParser
from shutil import copytree, Error
from os import listdir, rename, walk, remove
from os.path import expanduser, join, isdir, exists, basename, abspath


RULES_FILE = '.rules.py'
MAREK_PATH = [
    "/usr/share/marek",
    expanduser("~/.marek")
]


def get_available_templates():
    dirs = {}
    for tdir in reversed(TEMPL_PATH):
        if not (tdir and exists(tdir)):
            continue
        for template in listdir(tdir):
            template_dir = join(tdir.rstrip("/"), template)
            if not isdir(template_dir):
                continue
            dirs[template] = template_dir
    return dirs


def render_string_template(template, data):
    from string import Template
    return Template(string).safe_substitute(**data)


def load_rules(template_path, project_name, quiet):
    rules_file = join(template_path, RULES_FILE)
    if not os.path.exists(rules_file):
        return None
    import __builtin__
    __builtin__.project_name = basename(clone_path)
    __builtin__.quiet = quiet
    rules = load_source('rules', rules_file)
    del(__builtin__.project_name)
    del(__builtin__.quiet)
    return rules


def process_clone(clone_path, rules):
    # init string processing function and template dict
    render_string_template = getattr(rules, "render_string_template", render_string_template)
    data = getattr(rules, "data", {})
    # process files and dirs
    for path, dirs, files in walk(clone_path):
        # process dirs
        for tdir in list(dirs):
            ndir = render_string_template(tdir, data)
            if tdir != ndir:
                rename(join(path, tdir), join(path, ndir)):
                dirs.remove(tdir)
                dirs.append(ndir)
        # process files
        for tfile in files:
            old_name = join(path, tfile)
            with open(old_name, "r+") as f:
                info = render_string_template(f.read(), data)
                f.seek(0)
                f.write(info)
            new_name = render_string_template(old_name, data)
            if old_name != new_name:
                rename(old_name, new_name)


def process_template(template_name, project_name, quiet=False):
    try:
        assert template_name
        assert project_name
        clone_path = abspath(project_name)
        template_path = get_available_templates()[template_name]
        copytree(template_path, clone_path)
        process_clone(clone_path, load_rules(template_path, project_name, quiet))
    except AssertionError:
        print "Please specify a source template and project name."
        sys.exit(1)
    except KeyError:
        print "Template %s was not found" % template_name
        sys.exit(1)
    except Error, e:
        print "Cloning error: %s" % e
        sys.exit(1)
    except KeyboardInterrupt:
        print >> sys.stderr, "\nInterrupted"
        sys.exit(1)


def show_templates():
    print "Avaliable templates:"
    for template in sorted(get_available_templates().values()):
        print template
    sys.exit(0)


def main():
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
