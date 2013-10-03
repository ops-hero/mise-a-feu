import unittest
from mock import patch

with patch('fabric.api.sudo') as sudo_mock:
    from mise_a_feu.lib.stack_updater import StackUpdater

def run_single_assert_command(updater, command):
    updater.run()
    sudo_mock.assert_called_with(command)
    sudo_mock.reset_mock()


class StackUpdaterTestCase(unittest.TestCase):

    def test_run(self):
        run_single_assert_command(StackUpdater("default",
                                               "1.2.3",
                                               "buildhost-64",
                                               "/etc/manifests.cfg"),
            "/root/tools/update_stack.py /etc/manifests.cfg buildhost-64 default 1.2.3")

        run_single_assert_command(StackUpdater("default",
                                               "1.2.3",
                                               "buildhost-64",
                                               "/etc/manifests.cfg",
                    updater_path="/tmp/update_stack.py"),
            "/tmp/update_stack.py /etc/manifests.cfg buildhost-64 default 1.2.3")

        run_single_assert_command(StackUpdater("default",
                                               "1.2.3",
                                               "buildhost-64",
                                               "/etc/manifests.cfg",
                    verbose=True),
            "/root/tools/update_stack.py --verbose /etc/manifests.cfg buildhost-64 default 1.2.3")

        run_single_assert_command(StackUpdater("default",
                                               "1.2.3",
                                               "buildhost-64",
                                               "/etc/manifests.cfg",
                    force_update=True),
            "/root/tools/update_stack.py --force /etc/manifests.cfg buildhost-64 default 1.2.3")

        run_single_assert_command(StackUpdater("default",
                                               "1.2.3",
                                               "buildhost-64",
                                               "/etc/manifests.cfg",
                    force_update=True, verbose=True),
            "/root/tools/update_stack.py --verbose --force /etc/manifests.cfg buildhost-64 default 1.2.3")

        run_single_assert_command(StackUpdater("default",
                                               "1.2.3",
                                               "buildhost-64",
                                               "/etc/manifests.cfg",
                                               webcallback="http://host.foo/bar",
                                               verbose=True),
            "/root/tools/update_stack.py --verbose --web-callback http://host.foo/bar /etc/manifests.cfg buildhost-64 default 1.2.3")

