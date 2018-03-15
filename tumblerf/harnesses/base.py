
class BaseHarness():
    def __init__(self):
        self.timeout = 50

    def set_timeout(self, timeout_ms):
        self.timeout = timeout_ms

    def open(self):
        pass

    def close(self):
        pass

    def __repr__(self):
        return "{}(reset={})".format(self.name, self.implements_reset())

    @property
    def name(self):
        return self.__class__.__name__

    def add_subparser(self, subparsers):
        """
        Register additional arguments that the harness needs to get from a command line tool.
        Optional to implement, but if it is implemented it must follow the example behaviors closely.
        :param subparsers: Subparser object created by argparse's parser.add_subparsers call.
        """
        return None

    def process_cli(self, parser, argv):
        """
        Parses available options at the command line and uses them to update internal options.
        :param parser: argparse.ArgumentParser object
        :param argv: Array of command line options
        """
        argv.insert(0, self.__class__.__name__)  # We add this as a convention to get the data to the right subparser.
        args, _ = parser.parse_known_args(argv)  # We may have options in argv meant for other tools, so we allow ignoring.
        # TODO: In your harness, override this function and use args to set internal state.

    def do_reset(self):
        """
        Reset the device to a clean state via reboot or other means. Returns True if succeeded, otherwise False.
        :return: boolean
        """
        raise NotImplementedError

    def implements_reset(self):
        """
        Returns true if the subclass implements do_reset(), thus indicating it can provide reset functionality.
        :return: bool
        """
        do_reset_attr = getattr(self, "do_reset", None)
        do_reset_base = getattr(BaseHarness, "do_reset", None)
        return callable(do_reset_attr) and do_reset_attr.__func__ != do_reset_base.__func__

    def is_valid(self):
        """
        This function returns True if the device is in an valid state, indicating a that it is operating
        as expected and no change from baseline (from fuzzing, etc) has been observed.
        This may return True, False, or None if the status is not able to be determined.
        :return: boolean or None
        """
        raise NotImplementedError

    def is_invalid(self):
        """
        This function returns True if the device is in an invalid state, indicating a potential
        crash or other event that may be a "positive" outcome of the fuzzing.
        It is a separate function instead of using "not is_valid()", because there may be different ways to
        check for these states. This may return True, False, or None if the status is not able to be determined.
        :return: boolean or None
        """
        raise NotImplementedError

    def make_simple_help(self, parser):
        message = parser.format_usage()
        message = message.split(self.__class__.__name__, 2)[1]
        return "\t{}:\t{}".format(self.__class__.__name__, message)
