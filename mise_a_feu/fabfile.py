#!/usr/bin/env python
#code: utf-8

import os
from fabric.api import put, task, run, sudo, settings, abort, local, env, runs_once, execute, parallel
import fabric.main

from lib.stack_updater import StackUpdater
from lib.utils import str2bool, get_config, run_notifications, log_deployment
from scripts.update_stack import get_version


# monkey patch this to load yaml
fabric.main.load_settings = get_config


@task
def version():
    """
    Print version of the package.
    """
    print get_version()


@task
def show_config():
    """
    Dummp settings.
    """
    for key in sorted(env.iterkeys()):
        print "%s: %s" % (key, env[key])


@task
def update_updater(updater_path=None):
    '''
    Upload a new update_stack python script to the REMOTE side (e.g. hosts)
    '''
    updater_path = updater_path or '/root/tools/update_stack.py'
    origin = os.path.join(os.path.dirname(__file__),
                        "scripts",
                        "update_stack.py")

    put(origin, updater_path, mirror_local_mode=False, use_sudo=True)
    sudo("chown root:root %s" % updater_path)
    sudo("chmod 770 %s" % updater_path)


@task
def run_updater(stack, buildhost,
                manifest=None, updater_path=None, webcallback=None,
                verbose=True, force=False):
    '''
    Run the REMOTE update_stack python script using a REMOTE manifest
    '''
    verbose = str2bool(verbose)
    force = str2bool(force)

    updater = StackUpdater(stack,
                           buildhost,
                           manifest=manifest,
                           updater_path=updater_path,
                           webcallback=webcallback,
                           force_update=force,
                           verbose=verbose)
    return updater.run()


@task
@parallel
def deploy_host(stack_version):
    """
    Do only deployment according to config file & stack version
    """
    run_updater(stack_version, env["buildhost"])


@task
def post_deploy():
    """
    Run post deployment tasks
    """
    for command in env["post_deployment"]:
        if ("run_once_on" in command and
                env.host_string != command["run_once_on"]):
            continue
        else:
            with settings(warn_only=command["warn_only"] if "warn_only" in command else env.warn_only):
                run(command["command"])


@task
@runs_once
def deploy(stack_version):
    """
    Deploy to all the hosts and run the post deployment tasks.
    """
    # LOCK the deploymend with pidfile here, req for paralel execution!
    if os.path.exists(os.path.expanduser(env["pidfile"])):
        abort("Deployment in progress: %s" % env["pidfile"])
    with open(os.path.expanduser(env["pidfile"]), "w") as pidfile:
        pidfile.write(str(os.getpid()))

    run_notifications(env.notifications["start"], stack_version)
    # TODO? with settings(warn_only=True):
    execute(deploy_host, stack_version)
    execute(post_deploy)
    log_deployment(stack_version)
    # unlock here
    os.remove(os.path.expanduser(env["pidfile"]))
    run_notifications(env.notifications["end"], stack_version)


def main():
    """
    Allow the execution of the fabfile in standalone.
    even as entry_point after installation via setup.py.
    """
    current_file = os.path.abspath(__file__)
    if current_file[-1] == "c":
        current_file = current_file[:-1]
    fabric.main.main([current_file])

if __name__ == '__main__':
    main()

