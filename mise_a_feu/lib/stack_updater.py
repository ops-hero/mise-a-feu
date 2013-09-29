from fabric.api import settings, sudo


def target_host(host):
    """
    Returns a fabric settings manager with the host_string setting set to the
    given host.

    :param host: String with the target host name with the form
        ``[user@]host[:port]``
    """
    return settings(host_string=host)


class StackUpdater(object):
    """
    Run the update script on an host remotely.

    Basic usage:

        updater = StackUpdater(stack="1.2.3",
                               buildhost="buildbot-64",
                               webcallback="http://somehost/foo/bar",
                               force_update=True,
                               verbose=False)
        for host in hosts_list:
            with settings(host_string=host):
                updater.run()
    """
    def __init__(self, stack, buildhost,
                 manifest=None, updater_path=None, webcallback=None,
                 force_update=False, verbose=False):
        self.stack = stack
        self.buildhost = buildhost
        self.manifest = manifest or "/root/tools/packages/manifests"
        self.updater_path = updater_path or "/root/tools/update_stack.py"
        self.webcallback = webcallback
        self.force_update = force_update
        self.verbose = verbose

    def run(self):
        command = '%s %s%s%s%s %s %s' % (self.updater_path,
            '' if not self.verbose else '--verbose ',
            '' if not self.force_update else '--force ',
            '' if not self.webcallback \
                                else '--web-callback %s ' % self.webcallback,
            self.manifest,
            self.buildhost,
            self.stack)
        return sudo(command)
