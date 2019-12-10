#!/usr/bin/env python3

import json
import logging
from pprint import pformat
from OTXv2 import OTXv2
from OTXv2 import IndicatorTypes

from sys import path
from os.path import dirname as dir
path.append(dir(path[0]))

import otrs_functions
from config import LoadConfig


def Main(IPList, TicketID):
    conf = LoadConfig.Load()
    otx = OTXv2(conf["api_keys"]["AlienVaultAPI"])
    for IP in IPList:
        logging.info("[AlienVault] OTX Searching %s" % IP)
        result = pformat(otx.get_indicator_details_full(IndicatorTypes.IPv4, IP))

        otrs_functions.UpdateTicket("","AlienVault OTX - %s Results" % IP, result, TicketID)

