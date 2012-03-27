class NoDefault(object): pass


class NoValueError(Exception): pass


def get_input(help_message, default=NoDefault):
    if default is not NoDefault and quiet:
        return default
    data = raw_input("%s [%s]: " % (help_message, str(default)))
    if not data and default is NoDefault:
        raise NoValueError("Value is missing.")
    return data or default
