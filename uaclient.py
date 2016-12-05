#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import socket
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import useragenthandler
import hashlib

"""
 COMPROBACION DE LA ENTRADA
"""
if len(sys.argv) != 4:
    sys.exit("Usage: python3 uaclient.py config method option")
     
_, CONFIG, METODO, OPCION = sys.argv

CONFIG = open(CONFIG, 'r')

"""
 INICIALIZA EL HANDLER
"""
parser = make_parser()
kHandler = useragenthandler.UserAgentHandler()
parser.setContentHandler(kHandler)
parser.parse(CONFIG)
data = kHandler.get_tags()

print('DATOS DICCIONARIO:')
print(data)

SERVER = data["regproxy_ip"]
PORT = int(data["regproxy_puerto"])
SIP = data["account_username"]+':'+data["uaserver_puerto"]

"""
 COMIENZA CONEXION
"""
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
    my_socket.connect((SERVER, PORT))

    if METODO == 'REGISTER':
        LINE = 'REGISTER sip: {} SIP/2.0\r\nExpires: {}\r\n'.format(SIP, OPCION)
        
    elif METODO == 'INVITE':
        LINE = 'INVITE sip: {} SIP/2.0\r\n'.format(OPCION)
        LINE += 'Content-Type: application/sdp' + '\r\n\r\n' 
        LINE += 'v = 0\r\n' 
        LINE += 'o = {} {}\r\n'.format(data["account_username"], data['uaserver_ip'])
        LINE += 's = MiSesion\r\n'
        LINE += 't = 0\r\n'
        LINE += 'm = audio {} RTP'.format(data['rtpaudio_puerto'])
        
    elif METODO == 'BYE': 
        LINE = 'BYE sip: {} SIP/2.0\r\n'.format(OPCION)
        
    print("Enviando:", LINE)
    my_socket.send(bytes(LINE, 'utf-8') + b'\r\n') ##
    
    dato = my_socket.recv(1024)
    datos = dato.decode('utf-8').split()
    print(dato.decode('utf-8'))
    
    if datos[1] == '401':
        nonce = datos[7]
        h = hashlib.sha1()
        h.update(bytes(data["account_passwd"], 'utf-8'))
        h.update(bytes(nonce, 'utf-8'))
        LINE = 'REGISTER sip:' + SIP + ' SIP/2.0\r\n' + 'Expires: ' + OPCION + '\r\n'
        LINE += 'Authorization: Digest response= {}'.format(h.hexdigest())
        print("Enviando:", LINE, '\r\n')
        my_socket.send(bytes(LINE, 'utf-8') + b'\r\n')
        
        dato = my_socket.recv(1024)
        datos = dato.decode('utf-8').split()
        print(dato.decode('utf-8'))

print("Socket terminado.")
