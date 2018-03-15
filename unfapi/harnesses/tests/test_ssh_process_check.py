import pytest
import subprocess
import os.path
import re

from ..ssh_process_check import SshProcessCheckHarness

class TestSshProcessHarness(object):
    """
    This requires the docker daemon to be started before using this test case.
    """
    docker_name = None

    def setup_method(self, method):
        """Setup any state tied to the execution of the given method in a class. Invoked for every test method."""
        if self.docker_name is not None:
            print("WARN: Docker instance was not reset")
        print("=== Setup SSH server for {}".format(method))
        ssh_pub_key = None
        script_path = os.path.dirname(os.path.realpath(__file__))
        try:
            res = subprocess.check_call(["docker", "build", script_path, "-t", "ssh-test", "--force-rm",
                                         "-f", os.path.join(script_path, "Dockerfile.ssh")])
            #print("Build:", res)
            res = subprocess.check_output(["docker", "run", "-d", "--name", "ssh-server", "-p", "8022:22", "ssh-test"])
            self.docker_name = str(res.strip())
            print("Started docker process:\t{}".format(self.docker_name))
            res = subprocess.check_output(["docker", "exec", "-i", "ssh-server", "/bin/bash", "-c",
                                           'echo -e "testpass\ntestpass" | passwd root'], stderr=subprocess.STDOUT)
            print("Set pass:", res)
        except subprocess.CalledProcessError as e:
            print(e)
            self.teardown_method(method)
            pytest.skip("Skipping test due to docker error.")
        except OSError as e:
            # We do not tear down as docker isn't installed and thus that too will fail.
            pytest.skip("Skipping test due to docker not being installed.")

    def teardown_method(self, method):
        """Teardown any state that was previously setup with a setup_method call."""
        print("INFO: Shutting down Docker instance.")
        try:
            res = subprocess.check_call(["docker", "stop", "ssh-server"])
            res = subprocess.check_call(["docker", "rm",   "ssh-server"])
            self.docker_name = None
        except subprocess.CalledProcessError as e:
            print(e)

    @pytest.fixture
    def ssh_process_harness(self, request):
        # TODO: Find a way to run without pytest -s invocation.
        # See https://github.com/pytest-dev/pytest/issues/1599 and https://github.com/pytest-dev/pytest/issues/2709
        # capmanager = pytestconfig.pluginmanager.getplugin('capturemanager')
        # capmanager.suspendcapture()

        print("=== Setup SshProcessCheckHarness (for {})".format(request.function.__name__))
        ssh_conn = SshProcessCheckHarness("127.0.0.1:8022", "root", "testpass")
        script_path = os.path.dirname(os.path.realpath(__file__))
        ssh_conn.set_key_filename(os.path.join(script_path, 'test-rsa.key'))
        yield ssh_conn

    def test_auth(self, ssh_process_harness):
        ssh_process_harness.set_process_regex(re.compile(r"ps$", re.MULTILINE))
        assert ssh_process_harness.is_valid()
