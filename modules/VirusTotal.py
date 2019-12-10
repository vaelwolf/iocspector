#!/usr/bin/env python3

import logging
import requests
import traceback
from time import sleep
from pprint import pformat

## Trick Path into loading main directory
from sys import path
from os.path import dirname as dir
path.append(dir(path[0]))

## Load OTRS functions and LoadConfig function
import otrs_functions as OTRS
from config import LoadConfig

def RequestIP(IP):

    ## Load Configuration and set VirusTotal configuration
    conf = LoadConfig.Load()
    url = 'https://www.virustotal.com/vtapi/v2/ip-address/report'
    params = { 'apikey': conf["api_keys"]["VirusTotalAPI"], 'ip': IP }

    ## Send Request to VirusTotal and Retrieve Response
    response = requests.get(url, params=params)

    ## Check if Response is valid
    if str(response) == "<Response [200]>":
        return response.json()
    
    ## If Response isn't valid (e.g. API limit exceeded), log this, wait a minute, then try again
    else:
        logging.info("VirusTotal API limit exceeded. Waiting 60 seconds to try again.")
        sleep(60)
        Request(IP)


def Main(IPAddressList, TicketID):

    ## Initialize Lists and other vars
    Leftovers = []
    count = 1

    ## Make a copy of the IP List
    IPList = IPAddressList.copy()

    ## Check if the IP List isn't empty, then iterate over it
    if IPList != []:
        for IP in IPList:

            ## If we haven't already done this four times (VirusTotal's current free tier API limit), proceed
            if count != 4:
                logging.info("[VirusTotal] Searching VirusTotal for IP %s" % IP)
  
                try:
                    ## Launch request function
                    response = RequestIP(IP)

                    ## If valid response code, proceed
                    if response['response_code'] == 1:
                        logging.info("[+] Updating Ticket")

                        ## Use pprint's pformat to make it readable
                        results = pformat(response)

                        ## Update Ticket with results
                        OTRS.UpdateTicket("", "VirusTotal Lookup - %s Results" % IP, results, TicketID)

                        ## Remove IP from the next-round list
                        IPList.remove(IP)

                    ## If no data was retrieved, update the ticket with nothing was found
                    else:
                        logging.info("[+] Result not found; Updating Ticket")
                        OTRS.UpdateTicket("", "VirusTotal Lookup - %s Not found" % IP, "No data found in Virustotal for IP: %s" % IP, TicketID)

                        ## Remove IP from next-round list
                        IPList.remove(IP)

                ## If VirusTotal API limit reached and couldn't get a response, update the ticket and send it to next round for scanning
                except KeyError:
                    logging.info("[+] VirusTotal KeyError - Sending to next iteration of scanning")
                    OTRS.UpdateTicket("", "VirusTotal Lookup - %s" % IP, "VirusTotal Public API limit reached for IP: %s" % IP + ". Marking %s and other IPs for the next scan." % IP, TicketID)
                    logging.info(traceback.print_exc())
                    Leftovers.append(IP)

                ## If an odd TypeError occurred, log the traceback and skip it
                except TypeError:
                    logging.info("[+] VirusTotal TypeError - no response received. Possible API limit reached.")
                    logging.info(traceback.print_exc())
                    pass

            ## Iterate the count, wait a second, then relaunch the script with the leftovers
            count += 1
            sleep(1)
        Leftovers.extend(IPList)
        if Leftovers != []:
            Main(Leftovers, TicketID)
            
