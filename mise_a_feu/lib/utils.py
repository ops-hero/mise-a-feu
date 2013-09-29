import datetime
import os
import yaml

from fabric.api import abort, local, env


def str2bool(answer):
    """
    Convert a parameter to boolean if possible.
    Fabfile arguments are most of time string.
    """
    if isinstance(answer, bool):
        return answer
    elif isinstance(answer, str):
        if 'false' == answer.lower():
            return False
        elif 'true' == answer.lower():
            return True

    raise Exception('Input value should be either \'True\' or \'False\'.')

def get_config(config_file):
    try:
        return yaml.load(file(config_file, 'r'))
    except IOError:
        abort("Please specify a config file ie. 'fab -c examples/foo.yml'")

def run_notifications(notifications, stack):
    for noti in notifications:
        message = noti["message"] % {"stack": stack}
        command = noti["command"] % {"message": message}
        local(command)

def log_deployment(stack, use_utc=False):
    strf_format = "%Y-%m-%d %H:%M:%S" if "strf_format" not in env else env.strf_format
    deployment_env = env.rcfile.split("/")[-1]
    timestamp = datetime.datetime.utcnow() if use_utc else datetime.datetime.now()
    line = "%s %s %s\n" % (timestamp.strftime(strf_format), deployment_env, stack)
    with open(os.path.expanduser(env.deployment_history), "a") as history_log:
        history_log.write(line)
