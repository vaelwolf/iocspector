#!/usr/bin/env python3

import logging
import sqlite3
from ipaddress import ip_address

import otrs_functions as OTRS

def Connect():
    database = "/opt/sqlite3/assets.db"
    table = "asset_list"

    conn = sqlite3.connect(database)
    db = conn.cursor()

    return db, table


def Search(db, table, IPAddressList):
    IPList = IPAddressList.copy()
    AssetData = []
    
    for IP in reversed(IPList):
        query = "SELECT ip_address, hostname, criticality FROM %s where ip_address = '%s'" % (table,IP)
        db.execute(query)
        data = db.fetchall()
        AssetData.append(data)

    return AssetData


def Main(IPAddressList, TicketID):

    # j[1] : database column 'hostname' value
    # j[2] : database column 'criticality' value

    logging.info("[AssetQuery] Starting database query")

    db, table = Connect()
    IPList = Search(db, table, IPAddressList)

    result = []

    for i in range(len(IPList)):
        for j in IPList[i]:
            result.append("IP searched is an asset with %s criticality - %s (%s)" % (j[2], j[0], j[1]))
            if j[2] == "High":
                NewPriority = 5
                OTRS.ChangePriority(5, "Critical Asset matched (%s) - IoCSpector has modified the priority to be %s" % (j[0], NewPriority), TicketID)
                logging.info(f"[AssetQuery] Found Critical Asset - {j[0]}")

    if result != []:
        OTRS.UpdateTicket("", "Matched Asset IP - Results", '\n'.join(result), TicketID)
        logging.info(f"[AssetQuery] Updating Ticket #{TicketID}")
    else:
        logging.info("[AssetQuery] No Assets discovered")

        return
