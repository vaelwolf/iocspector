#!/usr/bin/env python3
import os
import socket
import modules
import logging
import re as regex
from time import sleep
from threading import Thread
from ipaddress import ip_address
from importlib import import_module
from tendo import singleton as Check
from config import LogProfile, LoadConfig
from pyotrs import Article, Client, Ticket


def LoginOTRS(TicketID):

    ## Stage Configuration file for Login Parameters
    client = LoadConfig.Stage()

    ## Create Session and Get Ticket Data
    client.session_create()
    ticket = client.ticket_get_by_id(TicketID, articles=True)
    
    return client, ticket


def SearchOTRS(ticket):

    ## Initialize Lists
    IPAddressList = []
    IPListDeduped = []

    logging.info("[SearchOTRS] Grabbing Ticket Articles")

    ## Get Latest Ticket (n-1) and parse through it for an IPv4 Address 
    ArticleNum = (len(ticket.to_dct()["Ticket"]["Article"]) - 1)
    if ticket.to_dct()["Ticket"]["Article"][ArticleNum]["From"] != "IoCSpector API":
        body = (ticket.to_dct()["Ticket"]["Article"][ArticleNum]["Body"])

        IP = regex.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', body)
        IPAddressList.extend(IP)

    ## Deduplicate IP Address List using List Comprehension
    [IPListDeduped.append(i) for i in IPAddressList if i not in IPListDeduped]

    ## Log to file how many IPs were found
    logging.info("[SearchOTRS] Found %s IP addresses in ticket articles" % len(IPListDeduped))

    return IPListDeduped


def CreateSocket():

    ## Load Configuration File
    conf = LoadConfig.Load()

    ## Log that IoCSpector is listening on the configuration-defined port
    logging.info(f"[IoCSpector] Listening on port {conf['LPort']}")

    ## Start Socket Listener on Port from Configuration Port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((socket.gethostname(), conf['LPort'])) 
    s.listen(1)
    
    ## Receive Connections
    conn, address = s.accept()

    ## Start Multithreading to accept multiple incoming connections
    Thread(target=ProcessRequest, args=(conn, conf)).start()

    ## Close the Socket
    s.close()


def ProcessRequest(conn, conf):
    
    ## Initialize Lists
    PublicAddressList = []

    ## Log that a connection is received and store data into variable
    logging.info("[ProcessRequest] Connection received")
    data = conn.recv(1024).decode("ascii") 

    ## Parse out Ticket ID Sent from OTRS
    TicketID = regex.search(r'TicketID\"\:\"(\d+)', data).group(1)
    logging.info(f"[ProcessRequest] Ticket ID is {TicketID}")
    
    ## Check if Ticket ID exists and launch APIs
    if TicketID is not None:
        Client, Ticket = LoginOTRS(TicketID)
        logging.info("[ProcessRequest] Socket Closed and Ticket retrieved")
    
        ## Get IP Address List from OTRS Ticket
        IPAddressList = SearchOTRS(Ticket)

        ## Use List Comprehension to pull out any RFC1918 (private) addresses
        [PublicAddressList.append(PublicIP) for PublicIP in IPAddressList if not ip_address(PublicIP).is_private]

        ## Iterate over Configuration modules
        for module, values in conf['modules'].items():

            ## If user has chosen to load this module, import it
            if values[0] == True:
                Module = import_module(f'modules.{module}')
                logging.info(f"[IoCSpector] Importing {Module.__name__} from {Module.__file__}")

                ## If user has designated this module as being able to handle RFC1918 (private IPs), launch module
                if values[1] == 'Private':
                    Module.Main(IPAddressList, TicketID)

                ## Else if the module can only handle Public IPs (like AlienVault OTX), launch module with Public Address List
                else:
                    Module.Main(PublicAddressList, TicketID)

            ## If the user has chosen to not load this module, log that we're skipping it
            else:
                logging.info(f"[IoCSpector] Skipping {module} from configuration file")
    
    ## Log that this iteration is finished
    logging.info(f"[IoCSpector] Finished updating Ticket #{TicketID}\n")

    ## Wait 3 seconds before opening another socket
    sleep(3)
    CreateSocket()


if __name__ == '__main__':

    ## Check if another instance is running and kill process if it is
    logging.info(f"[PID: {os.getpid()} Checking if another instance is running...")
    try:
        self = Check.SingleInstance()
    except:
        exit()

    ## Welcome Greeting
    logging.info("[IoCSpector] Welcome to IoCSpector!")
    logging.info("[IoCSpector] Author: J. Checchi")
    logging.info("[IoCSpector] All rights reserved")

    ## Load Configuration File and iterate through values
    conf = LoadConfig.Load()
    for module, value in conf['modules'].items():
        if value[0] == True:
            logging.info(f"[+] Loaded Module '{module}' from configuration file")
        else:
            logging.info(f"[+] Skipping Module '{module}' from configuration file")

    ## Launch Main Socket Listener (starts program from this function)
    CreateSocket()
