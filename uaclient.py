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

fich = open(CONFIG, 'r')

parser = make_parser()
kHandler = clienthandler.ClientHandler()
parser.setContentHandler(kHandler)
parser.parse(fich)
data = kHandler.get_tags()

print('DATOS DICCIONARIO:')
print(data)
