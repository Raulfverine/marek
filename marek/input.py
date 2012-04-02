from marek import project


class NoValueError(Exception): pass


def get_input(help_message, default=None):
    if default is not None and project.quiet:
        return default
    data = raw_input("%s [%s]: " % (help_message, str(default)))
    if not data and default is None:
        raise NoValueError("Value is missing.")
    return data or default
