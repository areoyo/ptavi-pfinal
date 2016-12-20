#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import socketserver
import os
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import useragenthandler
import hashlib

"""
 COMPROBACION DE LA ENTRADA
"""
if len(sys.argv) != 2:
    sys.exit("Usage: python3 uaserver.py config")
_, CONFIG = sys.argv


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


class EchoHandler(socketserver.DatagramRequestHandler):

    def handle(self):
        # Escribe dirección y puerto del cliente (de tupla client_address)
        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read()
            datos = line.decode('utf-8').split()
            print(line.decode('utf-8'))
            # Si no hay más líneas salimos del bucle infinito
            if not line:
                break

            if datos[0] == "INVITE":
                self.wfile.write(b"SIP/2.0 100 Trying" + b"\r\n")
                self.wfile.write(b"SIP/2.0 180 Ring" + b"\r\n")
                LINE = 'SIP/2.0 200 OK\r\n'
                LINE += 'Content-Type: application/sdp' + '\r\n\r\n' 
                LINE += 'v = 0\r\n' 
                LINE += 'o = {} {}\r\n'.format(data["account_username"], \
                         data['uaserver_ip'])
                LINE += 's = MiSesion\r\n'
                LINE += 't = 0\r\n'
                LINE += 'm = audio {} RTP\r\n'.format(data['rtpaudio_puerto'])
                self.wfile.write(bytes(LINE,'utf-8'))
            if datos[0] == "ACK":
                aEjecutar = "./mp32rtp -i " + IP + " -p 23032 < " + FICH
                print("Vamos a ejecutar ", aEjecutar)
                os.system(aEjecutar)
            if datos[0] == "BYE":
                self.wfile.write(b"\r\n" + b"SIP/2.0 200 OK" + b"\r\n")
            elif datos[0] != "INVITE" or "BYE" or "ACK":
                self.wfile.write(b"SIP/2.0 405 Method Not Allowed" + b"\r\n")
            else:
                self.wfile.write(b"SIP/2.0 400 Bad Request" + b"\r\n")

if __name__ == "__main__":
    serv = socketserver.UDPServer((SERVER, PORT), EchoHandler)
    print("Listening...")
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")
