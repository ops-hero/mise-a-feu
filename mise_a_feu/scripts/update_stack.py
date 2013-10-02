#!/usr/bin/env python

import os
import argparse
import subprocess
import urllib2
import urllib
import json


base_folder = "/tmp"
is_verbose = False

__version__ = "0.0.1"


def get_version():
    """
    Version for Mise-a-feu package.
    """
    return __version__


def main(manifest_file, buildhost, domain=None,
         verbose=False, force_install=False, stack=None, webcallback=None):
    """
    Main logic to update only packages that are installed.
    """
    global is_verbose
    is_verbose = verbose

    packages_to_install = {}

    installed_packages = get_installed_packages(manifest_file)

    for package in installed_packages:
        installed_version = get_local_version_for(package)
        future_version = get_remote_version_for(buildhost,
                                                package,
                                                domain,
                                                stack=stack)

        if force_install or (installed_version != future_version):
            file_name = get_updated_package_name(buildhost,
                                                 package,
                                                 future_version)
            download_package(buildhost, file_name)
            packages_to_install[package] = file_name

    if len(packages_to_install) > 0:
        remove_packages(packages_to_install)
        install_packages(packages_to_install)

    if webcallback:
        _do_web_callback(webcallback, packages_to_install.keys())

    return packages_to_install


def log(message, log_level="INFO"):
    """
    Log messages according to setup. TODO logging file and level.
    """
    if is_verbose:
        print log_level + " - " + message


def get_installed_packages(manifest_file):
    """
    Retrieve data from file.
    """
    log("reading from file: %s" % manifest_file)
    return [line.replace("\n", "") \
                        for line in open(manifest_file, 'r').readlines()]


def get_local_version_for(package):
    """
    Retrieve local version.
    """
    command = "dpkg -s %s | grep Version | awk '{print $2}'" % package
    log("checking local version: %s" % command, log_level="DEBUG")
    version = subprocess.check_output(command,
                                    shell=True,
                                    universal_newlines=True).replace('\n', '')
    log("version found for %s: %s" % (package, version))
    return version


def get_remote_version_for(buildhost, package, domain, stack=None):
    """
    Retrieve remote version from the build server.
    Latest by default or from specific product stack.
    """
    stack = stack if stack else "latest"
    url = "http://%s/domains/%s/stacks/%s/packages/%s/version" % \
                                        (buildhost, domain, stack, package)
    log("getting version from: %s" % url, log_level="DEBUG")
    version = _read_from_url(url)
    log("version of %s for stack %s is %s" % (package, stack, version))
    return version


def get_updated_package_name(buildhost, package, future_version):
    url = "http://%s/packages/%s/version/%s/file" % \
                                        (buildhost, package, future_version)
    log("getting file name from: %s" % url, log_level="DEBUG")
    filename = _read_from_url(url)
    log("filename for %s in version %s is: %s" % \
                                        (package, future_version, filename))
    return filename


def download_package(buildhost, file_name):
    url = "http://%s/debs/%s" % (buildhost, file_name)
    final_file_name = os.path.join(base_folder, file_name)
    log("saving %s into %s" % (url, final_file_name), log_level="DEBUG")
    output = _retrieve_from_url(url, final_file_name)
    log("saved %s kb in %s" % (output, file_name))
    return output


def remove_packages(packages):
    command = "dpkg -r %s" % " ".join(sorted(packages.keys()))
    log("removing packages: %s" % command, log_level="DEBUG")
    return _shell_run(command)


def install_packages(packages):
    command = "dpkg --force-overwrite -i %s" % " ".join([os.path.join(base_folder, pkg) \
                                       for pkg in sorted(packages.values())])
    log("installing packages: %s" % command, log_level="DEBUG")
    return _shell_run(command)


# Helpers (to be patched)

def _read_from_url(url):
    f = urllib2.urlopen(url)
    return f.read().replace("\n", "")


def _shell_run(command):
    return subprocess.call(command, shell=True)


def _retrieve_from_url(url, filename):
    return urllib.urlretrieve(url, filename)


def _do_web_callback(web_callback_url, packages):
    """
    Make a POST HTTP request to callback url once the stack update is complete.
    Body of the request should be json data:
    {"packages" : [name+]}
    """
    payload = {"packages" : packages}
    req = urllib2.Request(web_callback_url,
                          json.dumps(payload),
                          {"content-type": "application/json"})

    try:
        f = urllib2.urlopen(req)
        return f.code == 200
    except urllib2.URLError, e:
        log("failed to open web callback %s : %s" % (web_callback_url, e),
            log_level="ERROR")
        return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Upgrade packages of the stack according to version.', prog="mise-a-feu (client)")
    parser.add_argument('--version', action='version', version='%(prog)s '+get_version())
    parser.add_argument('--test', action='store_true')
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--web-callback', action='store', dest='webcallback')
    parser.add_argument('manifests', type=file)
    parser.add_argument('buildhost', help="buildserver domain name to retrieve the data remotely")
    parser.add_argument('domain', nargs="?", default="default", help='Domain ("default" by default)')
    parser.add_argument('stack', nargs="?", default="latest", help='Stack version (latest version by default)')
    args = parser.parse_args()

    if not args.test:
        # run main action
        args.manifests.close()
        main(manifest_file=args.manifests.name,
             buildhost=args.buildhost,
             verbose=args.verbose,
             force_install=args.force,
             domain=args.domain,
             stack=args.stack,
             webcallback=args.webcallback)

    else:
        # helper functions for tests
        # need to have mock library installed: `pip install mock`
        from mock import patch
        from contextlib import nested
        import platform
        import tempfile

        def get_lookup_function(dict_arg):
            def _f(*input_):
                dict_arg_ = dict_arg
                for key in input_:
                    if key in dict_arg_:
                        if isinstance(dict_arg_[key], dict):
                            dict_arg_ = dict_arg_[key]
                        else:
                            return dict_arg_[key]
                    else:
                        raise KeyError("unexpected input %s" % key)
            return _f

        # run tests

        output = get_local_version_for("python")
        if not platform.platform().startswith("Darwin"):
            assert output in ['2.7.3-0ubuntu2', '2.7.3-0ubuntu2.2'], "local version '%s' does not match requirements" % output

        # run other tests

        with patch('__main__._read_from_url', get_lookup_function({"http://buildhost/domains/default/stacks/latest/packages/test-package/version": "1.0.0"})):
            output = get_remote_version_for("buildhost", "test-package", "default")
        assert output=='1.0.0', "can not retrieve remote version of a package %s" % output

        with patch('__main__._read_from_url', get_lookup_function({"http://buildhost/domains/default/stacks/123/packages/test-package/version": "1.0.1"})):
            output = get_remote_version_for("buildhost", "test-package", "default", stack="123")
        assert output=='1.0.1', "can not retrieve remote version of a package for a specific stack %s" % output

        # run other tests

        with patch('__main__._read_from_url', get_lookup_function({"http://buildhost/packages/test-package/version/1.2.3/file": "test-package-1.0.0-amd64.deb"})):
            output = get_updated_package_name("buildhost", 'test-package', '1.2.3')
        assert output=="test-package-1.0.0-amd64.deb", " %s" % output 

        # run tests for downloader

        with patch('__main__._retrieve_from_url', get_lookup_function({"http://buildhost/debs/test-package-1.0.0-amd64.deb": {"/tmp/test-package-1.0.0-amd64.deb": 10}})):
            output = download_package("buildhost", "test-package-1.0.0-amd64.deb")
        assert output>0, "can not download file"

        # run test for remove packages

        with patch('__main__._shell_run', get_lookup_function({"dpkg -r test-package": 0})):
            packages = {'test-package': 'test-package-1.0.0-amd64.deb'}
            output = remove_packages(packages)
        assert output==0, "command failed"

        with patch('__main__._shell_run', get_lookup_function({"dpkg -r test-package test2-package": 0})):
            packages = {'test-package': 'test-package-1.0.0-amd64.deb', 
                    'test2-package': 'test2-package-2.0.0-amd64.deb'}
            output = remove_packages(packages)
        assert output==0, "command failed"

        with patch('__main__._shell_run', get_lookup_function({"dpkg -r test-package test2-package": 0})):
            packages = {'test2-package': 'test2-package-2.0.0-amd64.deb', 
                    'test-package': 'test-package-1.0.0-amd64.deb'}
            output = remove_packages(packages)
        assert output==0, "command failed when package in other order"

        # run test for install packages

        with patch('__main__._shell_run', get_lookup_function({"dpkg --force-overwrite -i /tmp/test-package-1.0.0-amd64.deb": 0})):
            packages = {'test-package': 'test-package-1.0.0-amd64.deb'}
            output = install_packages(packages)
        assert output==0, "command failed"

        with patch('__main__._shell_run', get_lookup_function({"dpkg --force-overwrite -i /tmp/test-package-1.0.0-amd64.deb /tmp/test2-package-2.0.0-amd64.deb": 0})):
            packages = {'test-package': 'test-package-1.0.0-amd64.deb', 
                    'test2-package': 'test2-package-2.0.0-amd64.deb'}
            output = install_packages(packages)
        assert output==0, "command failed"

        with patch('__main__._shell_run', get_lookup_function({"dpkg --force-overwrite -i /tmp/test-package-1.0.0-amd64.deb /tmp/test2-package-2.0.0-amd64.deb": 0})):
            packages = {'test2-package': 'test2-package-2.0.0-amd64.deb', 
                    'test-package': 'test-package-1.0.0-amd64.deb'}
            output = install_packages(packages)
        assert output==0, "command failed when package in other order"

        # run test for the injectable shell runner

        output = _shell_run("echo foo > /dev/null")
        assert output==0, "runner failed to retrieve successful command"

        output = _shell_run("exit 2")
        assert output==2, "runner failed to retrieved failed command %s" % output

        # run tests for injectable url runner

        # one-shot webserver
        process = subprocess.Popen(["/bin/bash", "-c", 'nc -l 8000 <<< "hello world" > /dev/null'])
        from time import sleep; sleep(0.05)
        output = _read_from_url("http://127.0.0.1:8000/")
        assert output=="hello world", "runner failed to retrieve content from http server %s" % output

        # run tests for injectable downloader

        # one-shot webserver
        process = subprocess.Popen(["/bin/bash", "-c", 'nc -l 8000 <<< "hello world" > /dev/null'])
        from time import sleep; sleep(0.05)

        with  tempfile.NamedTemporaryFile() as fd:          
            output = _retrieve_from_url("http://127.0.0.1:8000/", fd.name)
            assert output>0, "downloader failed to retrieve url %s" % output
            output = fd.read()
            assert output=="hello world\n", "downloader failed to download file %s" % output

        # test file reader
        with  tempfile.NamedTemporaryFile(delete=False) as fd:
            fd.write("pkg1\npkg2")
            fd.close()
            output = get_installed_packages(fd.name)
            os.unlink(fd.name)
        assert output==['pkg1', 'pkg2'], "file reader failed to read data %s" % output

        # integration test

        with nested(
                patch('__main__.get_installed_packages', 
                        get_lookup_function({'toto.manifest': ['pkg1', 'pkg2']})),
                patch('__main__.get_local_version_for', 
                        get_lookup_function({'pkg1': "0.0.9", 'pkg2': "0.0.8"})),
                patch('__main__._shell_run', 
                        get_lookup_function({'dpkg -r pkg1 pkg2': 0,
                                        'dpkg --force-overwrite -i /tmp/pkg1-1.0.0-amd64.deb /tmp/pkg2-2.0.0-amd64.deb': 0,})),
                patch('__main__._read_from_url', 
                        get_lookup_function({'http://buildhost/domains/default/stacks/latest/packages/pkg1/version': "1.0.0",
                                        'http://buildhost/domains/default/stacks/latest/packages/pkg2/version': "2.0.0",
                                        "http://buildhost/packages/pkg1/version/1.0.0/file": "pkg1-1.0.0-amd64.deb",
                                        "http://buildhost/packages/pkg2/version/2.0.0/file": "pkg2-2.0.0-amd64.deb",})),
                patch('__main__._retrieve_from_url', 
                        get_lookup_function({"http://buildhost/debs/pkg1-1.0.0-amd64.deb": {"/tmp/pkg1-1.0.0-amd64.deb": 10},
                                            "http://buildhost/debs/pkg2-2.0.0-amd64.deb": {"/tmp/pkg2-2.0.0-amd64.deb": 10}})),
            ):
            output = main('toto.manifest', "buildhost", "default")
        assert output=={'pkg1': 'pkg1-1.0.0-amd64.deb', 'pkg2': 'pkg2-2.0.0-amd64.deb'}, "integration test failed %s" % output

        with nested(
                patch('__main__.get_installed_packages', 
                        get_lookup_function({'toto.manifest': ['pkg1', 'pkg2']})),
                patch('__main__.get_local_version_for', 
                        get_lookup_function({'pkg1': "1.0.0", 'pkg2': "0.0.8"})),
                patch('__main__._shell_run', 
                        get_lookup_function({'dpkg -r pkg2': 0,
                                        'dpkg --force-overwrite -i /tmp/pkg2-2.0.0-amd64.deb': 0,})),
                patch('__main__._read_from_url', 
                        get_lookup_function({'http://buildhost/domains/default/stacks/latest/packages/pkg1/version': "1.0.0",
                                        'http://buildhost/domains/default/stacks/latest/packages/pkg2/version': "2.0.0",
                                        "http://buildhost/packages/pkg2/version/2.0.0/file": "pkg2-2.0.0-amd64.deb",})),
                patch('__main__._retrieve_from_url', 
                        get_lookup_function({"http://buildhost/debs/pkg2-2.0.0-amd64.deb": {"/tmp/pkg2-2.0.0-amd64.deb": 10}})),
            ):
            output = main('toto.manifest', "buildhost", "default")
        assert output=={'pkg2': 'pkg2-2.0.0-amd64.deb'}, "integration test failed when 1 out 2 pkg need to be updated %s" % output

        with nested(
                patch('__main__.get_installed_packages', 
                        get_lookup_function({'toto.manifest': ['pkg1', 'pkg2']})),
                patch('__main__.get_local_version_for', 
                        get_lookup_function({'pkg1': "1.0.0", 'pkg2': "2.0.0"})),
                patch('__main__._read_from_url', 
                        get_lookup_function({'http://buildhost/domains/default/stacks/latest/packages/pkg1/version': "1.0.0",
                                        'http://buildhost/domains/default/stacks/latest/packages/pkg2/version': "2.0.0",})),
            ):
            output = main('toto.manifest', "buildhost", "default")
        assert output=={}, "integration test when no update needed failed %s" % output

        with nested(
                patch('__main__.get_installed_packages', 
                        get_lookup_function({'toto.manifest': ['pkg1', 'pkg2']})),
                patch('__main__.get_local_version_for', 
                        get_lookup_function({'pkg1': "1.0.0", 'pkg2': "2.0.0"})),
                patch('__main__._shell_run', 
                        get_lookup_function({'dpkg -r pkg1 pkg2': 0,
                                        'dpkg --force-overwrite -i /tmp/pkg1-1.0.0-amd64.deb /tmp/pkg2-2.0.0-amd64.deb': 0,})),
                patch('__main__._read_from_url', 
                        get_lookup_function({'http://buildhost/domains/default/stacks/latest/packages/pkg1/version': "1.0.0",
                                        'http://buildhost/domains/default/stacks/latest/packages/pkg2/version': "2.0.0",
                                        "http://buildhost/packages/pkg1/version/1.0.0/file": "pkg1-1.0.0-amd64.deb",
                                        "http://buildhost/packages/pkg2/version/2.0.0/file": "pkg2-2.0.0-amd64.deb",})),
                patch('__main__._retrieve_from_url', 
                        get_lookup_function({"http://buildhost/debs/pkg1-1.0.0-amd64.deb": {"/tmp/pkg1-1.0.0-amd64.deb": 10},
                                            "http://buildhost/debs/pkg2-2.0.0-amd64.deb": {"/tmp/pkg2-2.0.0-amd64.deb": 10}})),
            ):
            output = main('toto.manifest', "buildhost", "default", force_install=True)
        assert output=={'pkg1': 'pkg1-1.0.0-amd64.deb', 'pkg2': 'pkg2-2.0.0-amd64.deb'}, "failed when forced install %s" % output
