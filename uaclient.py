#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import socket
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import clienthandler

    
if len(sys.argv) != 4:
    sys.exit("Usage: python3 uaclient.py config method option")
     
_, CONFIG, METODO, OPCION = sys.argv

CONFIG = open(CONFIG, 'r')

parser = make_parser()
kHandler = clienthandler.ClientHandler()
parser.setContentHandler(kHandler)
parser.parse(CONFIG)
data = kHandler.get_tags()

print('DATOS DICCIONARIO:')
print(data)

SERVER = data["regproxy_ip"]
PORT = data["regproxy_puerto"]

if METODO == 'REGISTER':
    LINE = 'REGISTER sip:' + data["account_username"]+':'+data["uaserver_puerto"]+ ' SIP/2.0\r\n' + 'Expires: ' + OPCION + '\r\n\r\n'

print("Socket terminado.")
