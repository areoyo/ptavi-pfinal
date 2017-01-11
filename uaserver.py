#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import socketserver
import socket
import os
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import useragenthandler
import hashlib
import time

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

SERVER = data["uaserver_ip"]
PORT = int(data["uaserver_puerto"])
SIP = data["account_username"]+':'+data["uaserver_puerto"]
fich_log = data["log_path"]
AUDIO = data["audio_path"]
PROXY_IP = data["regproxy_ip"]
PROXY_PORT = int(data["regproxy_puerto"])

"""
FICHERO LOG
"""
def log (opcion, accion):
    fich = open (fich_log, 'a')
    hora = time.strftime('%Y%m%d%H%M%S', time.gmtime(time.time()))
    if opcion != 'empty':
        log_datos = str(PROXY_IP) + ':' + str(PROXY_PORT) + ' '
        if accion == 'snd':
            status = ' Sent to ' + log_datos
        elif accion == 'rcv':
            status = ' Received from ' + log_datos
        fich.write(hora + status + opcion.replace('\r\n',' ')+ '\r\n')
    else:
        if accion == 'start':
            status = ' Starting...'
        elif accion == 'finish':
            status = ' Finishing.'
        fich.write(hora  + status + '\r\n')

class EchoHandler(socketserver.DatagramRequestHandler):
    rtp_list = []
    def handle(self):
        # Escribe dirección y puerto del cliente (de tupla client_address)
        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read()
            datos = line.decode('utf-8').split()
            # Si no hay más líneas salimos del bucle infinito
            if not line:
                break
            log(line.decode('utf-8'),'rcv')
            
            if datos[0] == "INVITE":
                self.wfile.write(b"SIP/2.0 100 Trying" + b"\r\n")
                self.wfile.write(b"SIP/2.0 180 Ringing" + b"\r\n")
                LINE = 'SIP/2.0 200 OK\r\n'
                LINE += 'Content-Type: application/sdp' + '\r\n\r\n' 
                LINE += 'v = 0\r\n' 
                LINE += 'o = {} {}\r\n'.format(data["account_username"], \
                         data['uaserver_ip'])
                LINE += 's = MiSesion\r\n'
                LINE += 't = 0\r\n'
                LINE += 'm = audio {} RTP\r\n'.format(data['rtpaudio_puerto'])
                self.wfile.write(bytes(LINE,'utf-8'))
                log(LINE,'snd')
                self.rtp_list.append(datos[17])
                
            elif datos[0] == 'ACK':
                """
                Enviamos RTP
                """
                
                print("RTP")
                aEjecutar = "./mp32rtp -i " + self.rtp_list[0] + " -p 23032 < " + AUDIO
                print("Vamos a ejecutar ", aEjecutar)
                os.system(aEjecutar)
                print("FIN DE TRANSMISION RTP")
                self.rtp_list.clear()
            
            elif datos[0] != "INVITE" or "BYE" or "ACK":
                LINE = "SIP/2.0 405 Method Not Allowed\r\n"
                self.wfile.write(bytes(LINE))
                log(LINE,'snd')
            else:
                LINE = "SIP/2.0 400 Bad Request\r\n"
                self.wfile.write(bytes(LINE))
                log(LINE,'snd')
                
if __name__ == "__main__":
    serv = socketserver.UDPServer((SERVER, PORT), EchoHandler)
    print("Listening...")
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")
        log('empty','finish')
