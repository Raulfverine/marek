import os
import argparse
import shutil
from subprocess import check_call as call


clone = shutil.copytree


def normalize(file_name):
    """
    @file_name(string): file name to normalize
    @returns: absolute file name (starts with /)
    """
    if file_name.startswith("~"):
        file_name = os.path.expanduser(file_name)
    elif file_name.startswith("/"):
        pass
    else:
        file_name = os.path.abspath(file_name)
    return file_name


def substitute(directory, tpl_conf):
    """
    1. Read the template config
    The config is a dict/map:
    {
        "string_to_replace": "replacement",
        ...
    }
    2. Open the config for editing (some values are needed to be typed, some are dynamically calculated)
    3. Perform the replacement both inside the files and directory names
    4. Call the post_replacement
    """
    project_name = directory.split(os.path.sep)[-1:]


def existing_dir(dir_name):
    dir_name = normalize(dir_name)
    if not os.path.exists(dir_name):
        raise argparse.ArgumentTypeError("Directory %s does not exist" % dir_name)
    return dir_name


def dir_to_create(dir_name):
    dir_name = normalize(dir_name)
    if os.path.exists(dir_name):
        raise argparse.ArgumentTypeError("Directory %s already exists" % dir_name)
    parent_dir = os.path.dirname(dir_name)
    if not os.path.exists(parent_dir)
        raise argparse.ArgumentTypeError("Parent directory %s does not exist" % parent_dir)
    return dir_name


def main():
    choices = tools.keys()
    #
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument("--to", metavar="TO", type=dir_to_create, nargs="?", required=True,
                        help="To which place to clone the project.")
    parser.add_argument("--from", metavar="FROM", type=existing_dir, nargs="?",
                        help="From which place to clone the project.")
    parser.add_argument("--tpl-conf", metavar="CONF", type=str, nargs="?",
                        default="tpl.conf",
                        help="Name of the file in the project directory from which data should be taken "
                             "for substitution. The path is relative to project root.")
    #
    args = parser.parse_args()
    clone(args.from, args.to)
    substitute(args.to, args.tpl_conf)


if __name__ == "__main__":
    main()
