import fabric.network
from fabric.api import run, env
from re import _pattern_type as RE_PATTERN_TYPE

from .base import BaseHarness

class SshProcessCheckHarness(BaseHarness):
    def __init__(self, ssh_host=None, ssh_user=None, ssh_pass=None):
        BaseHarness.__init__(self)
        self.set_host(ssh_host, ssh_user)
        self.set_pass(ssh_pass)
        self.ps_cmd = None
        self.ps_regex = None

    def set_host(self, hostname, username):
        """
        Set the target of the connection.
        :param hostname: To connect to a port other than 22, provide "hostname:8022" or similar.
        :param username: If provided, is prepended to the hostname with an "@" sign.
        :return:
        """
        self.ssh_host = hostname
        self.ssh_user = username
        if self.ssh_user is None:
            env.host_string = hostname
        else:
            env.host_string = "{}@{}".format(self.ssh_user, self.ssh_host)

    def set_user(self, username):
        self.ssh_user = username

    def set_pass(self, password):
        self.ssh_pass = password
        env.password = self.ssh_pass

    def set_key_filename(self, key_filename):
        env.key_filename = key_filename

    def set_timeout(self, timeout_ms):
        self.timeout = timeout_ms
        env.timeout = self.timeout

    def set_process_regex(self, regex, ps_cmd="ps"):
        """
        This is required to be called on this harness, which needs to know how to inspect the `ps` output from the
        target system and
        :param regex: A Python compiled regex that will be searched against the process list on the target.
            Construct via "re.compile(pattern)" or similar.
        :param ps_cmd: If the system supports "ps aux" or similar, override the default "ps" here.
        :return:
        """
        if not isinstance(regex, RE_PATTERN_TYPE):
            raise ValueError("Invalid type passed in for regex argument.")
        self.ps_regex = regex
        self.ps_cmd = ps_cmd

    def __connect_and_run(self, command):
        try:
            res = run(command)
        finally:
            fabric.network.disconnect_all()
        return res

    def do_reset(self):
        """
        Reset the device to a clean state via reboot or other means. Returns True if succeeded, otherwise False.
        :return: boolean
        """
        raise NotImplementedError

    def is_valid(self):
        """
        This function connects to the device via SSH and checks to see if the expected process is running.
        :return: boolean or None
        """
        if self.ps_regex is None:
            raise ValueError("Must call set_process_regex() on harness.")
        ps_res = self.__connect_and_run(self.ps_cmd)
        print(ps_res)
        return self.ps_regex.search(ps_res) is not None

    def is_invalid(self):
        """
        In this simple harness, this is simply the inverse of is_valid() as the check is reliable.
        :return: boolean or None
        """
        is_valid = self.is_valid()
        return None if is_valid is None else not is_valid
