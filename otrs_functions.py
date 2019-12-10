#!/usr/bin/env/python3

import csv
import logging
from time import sleep
from config import LoadConfig
from pyotrs import Client, Article, Ticket

from iocsoar import LoginOTRS

def UpdateTicket(IP, Website, IoCData, TicketID):
    client, ticket = LoginOTRS(TicketID)

    updatedArticle = Article({ "Owner": "IoCSpector", "Subject": IP + " " + Website, "Body": "<html><body><pre>" + IoCData + "</pre></body></html>", "MimeType": "text/html" })
    client.ticket_update(TicketID, article=updatedArticle)


def ChangePriority(Level, Reason, TicketID):
    client, ticket = LoginOTRS(TicketID)

    client.ticket_update(TicketID, PriorityID=Level)
    UpdateTicket("", Reason, Reason, TicketID)


def CreateTicket(SIEM_Events):
    conf = LoadConfig.Load()
    client = Client("%s" % conf['otrs']['server'],
                    "%s" % conf['otrs']['user'],
                    "%s" % conf['otrs']['pass'])
    client.session_create()

    with open("siem_events.csv", "rt") as events:
        data = csv.reader(events)
        for event in data:
            ticket = Ticket.create_basic(Title=event[0],
                                         Queue=event[1],
                                         State=event[2],
                                         Priority=event[3],
                                         CustomerUser=event[4])
            article = Article({"Subject": event[5], "Body": event[6]})
            logging.info(client.ticket_create(ticket, article))
            sleep(30)
