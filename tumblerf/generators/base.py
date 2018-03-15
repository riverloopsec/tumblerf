
class BaseTestCaseGenerator():
    def __init__(self, includes_phy=False, includes_mac=False):
        self.samples = []
        self.__includes_phy = includes_phy
        self.__includes_mac = includes_mac
        self.__constraints = {}

    def __repr__(self):
        return "{}(PHY={}, MAC={})".format(self.name, self.includes_phy, self.includes_mac)

    @property
    def name(self):
        return self.__class__.__name__

    def add_sample(self, sample):
        self.samples.append(sample)

    def add_samples(self, samples):
        #print(type(samples))
        self.samples.extend(samples)

    def add_subparser(self, subparsers):
        """
        Register additional arguments that the generator needs to get from a command line tool.
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
        # TODO: In your generator, override this function and use args to set internal state.

    def set_default_constraints(self, constraints):
        """
        Set to None to clear out defaults.
        :param constraints:
        :return:
        """
        if not isinstance(constraints, dict):
            raise ValueError("Constraints must be provided as a dictionary of key/values.")
        self.__constraints = constraints

    def set_default_constraint(self, constraint_name, constraint_value):
        """
        Adds a key/value pair to the default constraints internal dictionary, overwriting or adding.
        :param constraint_name:
        :param constraint_value:
        :return:
        """
        self.__constraints[constraint_name] = constraint_value

    @property
    def default_constraints(self):
        return self.__constraints

    def get_default_constraint(self, constraint_name, expected_type=str):
        """
        Returns the requested value from the constraints dictionary if it matches the expected type given.
        :param constraint_name: The key name in the constraints dictionary
        :param expected_type: a Python type such as str or int
        :return: value or None if not found or type is wrong.
        """
        if self.__constraints is not None and constraint_name in self.__constraints:
            if isinstance(self.__constraints[constraint_name], expected_type):
                return self.__constraints[constraint_name]
            else:
                print("WARN: Type of constraint {} did not match expectation.".format(constraint_name))
        return None

    @property
    def includes_phy(self):
        return self.__includes_phy

    @property
    def includes_mac(self):
        return self.__includes_mac

    def yield_control_case(self, count=1):
        """
        Is a Python generator which yields potential control cases.
        These can be transmitted to gauge if the environment is ready for testing.
        These should cause the expected "valid" behavior on the target, e.g., causing an ACK response.
        :yield: A byte array generated as a control case.
        """
        raise NotImplementedError

    def get_control_case(self):
        """
        Returns a single control case string.
        :return:
        """
        for cc in self.yield_control_case(count=1):
            return cc

    def yield_test_case(self, count, constraints=None):
        """
        Is a Python generator which yields potential test cases to use.
        Implementers of generators should override this class to produce the fuzzing data.
        :param constraints: Dictionary of constraints to apply. Optional for an implementing class to use.
        :yield: A byte array generated as a possible test case.
        """
        raise NotImplementedError

    def get_test_case(self, constraints=None):
        """
        Returns a single test case string.
        :param constraints: Dictionary of constraints to apply. Optional for an implementing class to use.
        :return: ()
        """
        for tc in self.yield_test_case(1, constraints=constraints):
            return tc

    def get_test_cases(self, count, constraints=None):
        """
        Return a list (of count number) of test cases.
        :param count: The number of items to return in the list.
        :param constraints: Dictionary of constraints to apply. Optional for an implementing class to use.
        :return: ()
        """
        result = []
        for tc in self.yield_test_case(count, constraints=constraints):
            result.append(tc)
        return result

    def make_simple_help(self, parser):
        message = parser.format_usage()
        message = message.split(self.__class__.__name__, 2)[1]
        return "\t{}:\t{}".format(self.__class__.__name__, message)
