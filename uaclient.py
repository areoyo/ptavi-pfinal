#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
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

print('DATOS DICCIONARIO:') ##
print(data) ##

SERVER = data["regproxy_ip"]
PORT = int(data["regproxy_puerto"])
SIP = data["account_username"]+':'+data["uaserver_puerto"]
fich_log = data["log_path"]
USER = data["account_username"]
AUDIO = data["audio_path"]

"""
FICHERO LOG
"""
def log (opcion, accion):
    fich = open (fich_log, 'a')
    hora = time.strftime('%Y%m%d%H%M%S', time.gmtime(time.time()))
    if opcion != 'empty':
        log_datos = str(SERVER) + ':' + str(PORT) + ' '
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
        elif accion == 'error':
            status ==' Error: No server listening at '+ SERVER + ' port ' + PORT
        fich.write(hora  + status + '\r\n')
 
"""
 COMIENZA CONEXION
"""       
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
    my_socket.connect((SERVER, PORT))

    log('empty','start')

    if METODO == 'REGISTER':
        try:
            LINE = 'REGISTER sip:{} SIP/2.0\r\nExpires: {}'.format(SIP, OPCION)
        except socket.error:
            log('empty','error')
        
    elif METODO == 'INVITE':
        try:
            LINE = 'INVITE sip:{} SIP/2.0\r\n'.format(OPCION)
            LINE += 'Content-Type: application/sdp' + '\r\n\r\n' 
            LINE += 'v = 0\r\n' 
            LINE += 'o = {} {}\r\n'.format(data["account_username"], \
                     data['uaserver_ip'])
            LINE += 's = MiSesion\r\n'
            LINE += 't = 0\r\n'
            LINE += 'm = audio {} RTP'.format(data['rtpaudio_puerto'])
        except socket.error:
            log('empty','error')
        
    elif METODO == 'BYE': 
        try:
            LINE = 'BYE sip: {} SIP/2.0'.format(OPCION)
        except socket.error:
            log('empty','error')
    my_socket.send(bytes(LINE, 'utf-8') + b'\r\n')
    log(LINE,'snd')
    
    dato = my_socket.recv(1024)
    datos = dato.decode('utf-8').split()
    log(dato.decode('utf-8'),'rcv')
        
    if datos[1] == '100' and datos[7] == '200':
        METODO = 'ACK'
        LINE = METODO + " sip:" + datos[16] + " SIP/2.0\r\n"
        my_socket.send(bytes(LINE, 'utf-8') + b'\r\n')
        log(LINE,'snd')
        print("RTP")
        aEjecutar = "./mp32rtp -i " + datos[17] + " -p 23032 < " + AUDIO
        print("Vamos a ejecutar ", aEjecutar)
        os.system(aEjecutar)
        puerto = datos[17]
        print("FIN DE TRANSMISION RTP")
        
    elif datos[1] == '401':
        nonce = datos[7]
        h = hashlib.sha1()
        h.update(bytes(data["account_passwd"], 'utf-8'))
        h.update(bytes(nonce, 'utf-8'))
        LINE = 'REGISTER sip:' + SIP + ' SIP/2.0\r\nExpires: ' + OPCION + '\r\n'
        LINE += 'Authorization: Digest response= {}'.format(h.hexdigest())
        my_socket.send(bytes(LINE, 'utf-8') + b'\r\n')
        log(LINE,'snd')
        
        dato = my_socket.recv(1024)
        datos = dato.decode('utf-8').split()
        log(dato.decode('utf-8'),'rcv')

log('empty','finish')
print("Socket terminado.")
