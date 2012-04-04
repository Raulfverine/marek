from marek import project


def get_input(help_message, default=None, transformer=None):
    """ Gets input from keyboard and processes it """
    if transformer:
        default = transformer(default)
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
    if transformer and data:
        trans_data = transformer(data)
        if data != trans_data:
            print "Your input was transformed from '%s' to '%s'" % (data, trans_data)
        data = trans_data
    return data or default
