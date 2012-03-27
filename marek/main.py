import os
import sys
import argparse
import shutil
import imp


RULES_FILE = '.rules.py'
TEMPL_PATH = [
    
]


def list_tpls():
    """
    @returns: (dict) {"tpl_name": "/path/to/tpl"}
    """
    dirs = {}
    for tdir in reversed(TEMPL_PATH):
        if not (tdir and os.path.exists(tdir)):
            continue
        for tpl in os.listdir(tdir):
            tpl_dir = os.path.join(tdir.rstrip("/"), tpl)
            if not os.path.isdir(tpl_dir):
                continue
            dirs[tpl] = tpl_dir
    return dirs


def proc_string(string, data):
    from string import Template
    s = Template(string)
    return s.safe_substitute(**data)


def proc_clone(clone_path, quiet):
    project_name = os.path.basename(clone_path)

    def rename(old, new):
        if old != new:
            os.rename(old, new)
            return True
        return False

    # load rules
    rules_file = os.path.join(clone_path, RULES_FILE)
    rules = None
    if os.path.exists(rules_file):
        # make project_name and quiet globals for the rules file exclusively
        import __builtin__
        __builtin__.project_name = project_name
        __builtin__.quiet = quiet
        rules = imp.load_source('rules', rules_file)
        del(__builtin__.project_name)
        del(__builtin__.quiet)
        # rules file is not needed in the clone
        for to_rem in [rules_file, "%sc" % rules_file]:
            os.remove(to_rem)
    # init string processing function and template dict
    process_string = getattr(rules, "process_string", proc_string)
    data = getattr(rules, "data", {})
    data.update({"project_name": project_name})
    # process files and dirs
    for path, dirs, files in os.walk(clone_path):
        # process dirs
        renamed_dirs = []
        for tdir in dirs:
            ndir = proc_string(tdir, data)
            if rename(os.path.join(path, tdir), os.path.join(path, ndir)):
                dirs.remove(tdir)
                renamed_dirs.append(ndir)
        dirs.extend(renamed_dirs)
        # process files
        for tfile in files:
            old_name = os.path.join(path, tfile)
            with open(old_name, "r+") as f:
                info = process_string(f.read(), data)
                f.seek(0)
                f.write(info)
            new_name = process_string(old_name, data)
            rename(old_name, new_name)


def proc_tpl(tpl_name, project_name, quiet=False):
    clone_path = os.path.abspath(project_name)
    try:
        tpl_path = list_tpls()[tpl_name]
    except KeyError:
        print "Template %s was not found" % tpl_name
        sys.exit(0)
    try:
        shutil.copytree(tpl_path, clone_path)
        proc_clone(clone_path, quiet)
    except shutil.Error, e:
        print "Cloning error: %s" % e
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-q', '--quiet', action='store_true', help='Use default values without asking')
    parser.add_argument('-l', '--list', action='store_true', help='Show available templates')
    parser.add_argument('template', nargs='?', default=None)
    parser.add_argument('project_name', nargs='?', default=None)

    opts = parser.parse_args()
    if opts.list:
        print "Avaliable templates:"
        for tpl in sorted(list_tpls().values()):
            print tpl
        sys.exit(0)

    if opts.template is None:
        print "Please specify a source template."
        sys.exit(1)

    try:
        proc_tpl(opts.template, opts.project_name, opts.quiet)
    except KeyboardInterrupt:
        print >> sys.stderr, "\nInterrupted"


if __name__ == "__main__":
    main()
