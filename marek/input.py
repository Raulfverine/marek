from marek import project


class NoValueError(Exception): pass


def get_input(help_message, default=None):
    if default is not None and project.quiet:
        return default
    if default is not None:
        help_message = "%s [%s]: " % (help_message, str(default))
    else:
        help_message = "%s: " % help_message
    data = raw_input(help_message)
    if not data and default is None:
        raise NoValueError("Value is missing.")
    return data or default
