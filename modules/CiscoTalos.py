#!/usr/bin/env/python3

import requests
import logging

import otrs_functions as OTRS

def Main(IPAddressList, TicketID):
    result = []
    url = "https://talosintelligence.com/documents/ip-blacklist"
    Talos = requests.get(url)

    ## Make a copy of the IP List
    IPList = IPAddressList.copy()

    if IPList != []:
        for IP in IPList:
            logging.info(f"[Talos] Searching Blacklist for IP {IP}")

            if IP in Talos.text:
                result.append("<p style=\"color:red; display:inline;\">Found IP %s in Talos Blacklist!" % IP + "</p>")
                logging.info(f"[Talos] {IP} Found! Updating Ticket ID #{TicketID}")
                NewPriority = 5
                OTRS.ChangePriority(NewPriority, "%s is Blacklisted - IoCSpector has modified the priority to be %s" % (IP, NewPriority), TicketID)
            else:
                result.append("IP %s Not Found" % IP)
                logging.info(f"[Talos] {IP} Not Found")

        OTRS.UpdateTicket("", "Cisco Talos Blacklist Results", '\n'.join(result), TicketID)
