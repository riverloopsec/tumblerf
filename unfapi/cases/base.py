"""
Implements the base case class that is extended by any test case runner.
"""

class BaseCase():
    def __init__(self, interface, harness, generator):
        """
        Constructs a class which will run through a test case and return results.
        :param interface: A subclass of BaseInterface, properly setup and ready for use.
        :param harness: A subclass of BaseHarness, properly setup and ready for use.
        :param generator: A subclass of BaseGenerator, properly setup and ready for use.
        """
        # TODO: Check issubclass for each.
        self.__interface = interface
        self.__harness = harness
        self.__generator = generator

    def __repr__(self):
        return "{}({}, {}, {})".format(self.__class__, self.__interface, self.__harness, self.__generator)

    @property
    def interface(self):
        return self.__interface

    @property
    def harness(self):
        return self.__harness

    @property
    def generator(self):
        return self.__generator

    def run_test(self):
        """
        Runs the test cases, and associated control cases, and returns a list of results.
        :return: A TestResultWrapper object containing TestResult objects documenting the output of each test
        """
        raise NotImplementedError
