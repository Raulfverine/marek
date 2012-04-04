from marek import project


def get_input(help_message, default=None):
    if default is not None and project.quiet:
        return default
    if default is not None:
        help_message = "%s [%s]: " % (help_message, str(default))
    else:
        help_message = "%s: " % help_message
    data = raw_input(help_message)
    while not data and default is None:
        print "There is not default for this placeholder. Please enter some value or cancel the creation process."
        data = raw_input("[mandatory] %s" % help_message)
    return data or default
