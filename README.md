mise-a-feu
===========

[![Build Status](https://travis-ci.org/ops-hero/mise-a-feu.png?branch=master)](https://travis-ci.org/ops-hero/mise-a-feu)

This library is used to deploy the stacks on the host server. This can be used either from the CLI (via Fabric or command) or from a Python code (by including the library).



USAGE
-----

Either via Fabric, once the working copy is checked out:

    $ cd mise_a_feu
    $ fab -l
    $ ...
    $ fab -H host1.example.com update_updater
    $ ...
    $ fab -H host1.example.com run_updater:default,1.2.3,buildhost,webcallback=http://host:8080/stacks/update
    $ ...

After installing the package, a binary `mise-a-feu` is also available. It exposes directly the fabric file:

    $ mise-a-feu -l
    $ ...
    $ mise-a-feu -c config_file deploy:stack_version
    $ ...
    $ mise-a-feu -c examples/example_config.yml deploy:main,0.0.1
    $ ...


Or in another python application, after installing the package as well:

    from mise_a_feu import StackUpdater

    updater = StackUpdater(domain="default",
                           stack="1.2.3",
                           buildhost="buildhost",
                           manifest="/etc/manifest.data",
                           webcallback="http://host:8080/stacks/update",
                           force_update=True,
                           verbose=False)
        for host in hosts_list:
            with settings(host_string=host):
                updater.run()

TODO
----
* asynchronous remote call to update_stack.py
