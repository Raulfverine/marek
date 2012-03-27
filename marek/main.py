""" Marek: tool for creating various projects from templates. """

import sys
import imp
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
        for tpl in listdir(tdir):
            tpl_dir = join(tdir.rstrip("/"), tpl)
            if not isdir(tpl_dir):
                continue
            dirs[tpl] = tpl_dir
    return dirs


def render_template(template, data):
    from string import Template
    return Template(string).safe_substitute(**data)


def load_rules(tpl_path, project_name, quiet):
    rules_file = join(tpl_path, RULES_FILE)
    #
    if not os.path.exists(rules_file):
        return None
    #
    import __builtin__
    __builtin__.project_name = basename(clone_path)
    __builtin__.quiet = quiet
    rules = imp.load_source('rules', rules_file)
    del(__builtin__.project_name)
    del(__builtin__.quiet)
    return rules


def proc_clone(clone_path, rules):

    def _ren(old, new):
        if old != new:
            rename(old, new)
            return True
        return False

    # init string processing function and template dict
    render_template = getattr(rules, "render_template", render_template)
    data = getattr(rules, "data", {})
    # process files and dirs
    for path, dirs, files in walk(clone_path):
        # process dirs
        renamed_dirs = []
        for tdir in dirs:
            ndir = render_template(tdir, data)
            if _ren(join(path, tdir), join(path, ndir)):
                dirs.remove(tdir)
                renamed_dirs.append(ndir)
        dirs.extend(renamed_dirs)
        # process files
        for tfile in files:
            old_name = join(path, tfile)
            with open(old_name, "r+") as f:
                info = process_string(f.read(), data)
                f.seek(0)
                f.write(info)
            new_name = process_string(old_name, data)
            _ren(old_name, new_name)


def proc_tpl(tpl_name, project_name, quiet=False):
    try:
        assert tpl_name
        assert project_name
        clone_path = abspath(project_name)
        tpl_path = get_available_templates()[tpl_name]
        copytree(tpl_path, clone_path)
        proc_clone(clone_path, load_rules(tpl_path, project_name, quiet))
    except AssertionError:
        print "Please specify a source template and project name."
        sys.exit(1)
    except KeyError:
        print "Template %s was not found" % tpl_name
        sys.exit(1)
    except Error, e:
        print "Cloning error: %s" % e
        sys.exit(1)
    except KeyboardInterrupt:
        print >> sys.stderr, "\nInterrupted"
        sys.exit(1)


def show_templates():
    print "Avaliable templates:"
    for tpl in sorted(get_available_templates().values()):
        print tpl
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
        proc_tpl(opts.template, opts.project_name, opts.quiet)


if __name__ == "__main__":
    main()
