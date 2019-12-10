#!/usr/bin/env/python3

import yaml
from pyotrs import Client

def Load():
    ## Put Absolute Path Here
    with open("/opt/iocspector/config/soarconf.yml", "r") as yamlfile:
        try:
            return yaml.safe_load(yamlfile)
        except yaml.YAMLError as exception:
            logging.warning(exception)


def Stage():
    conf = Load()

    client = Client("%s" % conf['otrs']['server'],
                    "%s" % conf['otrs']['user'],
                    "%s" % conf['otrs']['pass'])

    return client
