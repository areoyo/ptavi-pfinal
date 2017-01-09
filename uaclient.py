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
fich_log = data["log_path"]

"""
FICHERO LOG
"""

def log (self, opcion, accion):
    fich = open (fich_log, 'a')
    self.hora = time.strftime('%Y%m%d%H%M%S', time.gmtime(time.time()))
    if opcion != 'empty':
        if accion == 'snd':
            status = ' Sent to '
        elif accion == 'rcv':
            status = ' Received from '
        fich.write(self.hora + status + opcion.replace('\r\n',' ')+ '\r\n')
    else:
        if accion == 'start':
            status = ' Starting...'
        elif accion == 'finish':
            status = ' Finishing.'
        fich.write(self.hora + status + '\r\n')    
        elif accion == 'error':
            status == 'Error: No server listening at ' + IP + ' port ' + port
        fich.write(self.hora + status + '\r\n')
 

"""
 COMIENZA CONEXION
"""       
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
    my_socket.connect((SERVER, PORT))
    
    # METODO LOG --> STARTING
    log('empty','start')

    if METODO == 'REGISTER':
        #try:
        LINE = 'REGISTER sip:{} SIP/2.0\r\nExpires: {}\r\n'.format(SIP, OPCION)
        
        # LLAMO EXCEPCION SOCKET.ERROR
        # EXCEPT SOCKET.ERROR:
            # METODO LOG --> ERROR
        
    elif METODO == 'INVITE':
        LINE = 'INVITE sip: {} SIP/2.0\r\n'.format(OPCION)
        LINE += 'Content-Type: application/sdp' + '\r\n\r\n' 
        LINE += 'v = 0\r\n' 
        LINE += 'o = {} {}\r\n'.format(data["account_username"], \
                 data['uaserver_ip'])
        LINE += 's = MiSesion\r\n'
        LINE += 't = 0\r\n'
        LINE += 'm = audio {} RTP'.format(data['rtpaudio_puerto'])
        # LLAMO EXCEPCION SOCKET.ERROR
        # EXCEPT SOCKET.ERROR:
            # METODO LOG --> ERROR
        
    elif METODO == 'BYE': 
        LINE = 'BYE sip: {} SIP/2.0'.format(OPCION)
        # LLAMO EXCEPCION SOCKET.ERROR
        # EXCEPT SOCKET.ERROR:
            # METODO LOG --> ERROR
        
    print("Enviando:", LINE, '\r\n')
    my_socket.send(bytes(LINE, 'utf-8') + b'\r\n') ##
    # METODO LOG  --> SENT TO
    log(LINE,'snd')
    
    dato = my_socket.recv(1024)
    datos = dato.decode('utf-8').split()
    print("Recibido: ", dato.decode('utf-8'), '\r\n')
    # METODO LOG --> RECEIVED FROM
    log(dato.decode('utf-8'),'rcv')
        
    if datos[2] == 'Trying' and datos[8] == 'OK':
        METODO = 'ACK'
        LINE = METODO + " sip:" + LOGIN + "@" + SERVER + " SIP/2.0\r\n"
        my_socket.send(bytes(LINE, 'utf-8') + b'\r\n')
        # METODO LOG --> SENT TO
        log(LINE,'snd')
        
    if datos[1] == '401':
        nonce = datos[7]
        h = hashlib.sha1()
        h.update(bytes(data["account_passwd"], 'utf-8'))
        h.update(bytes(nonce, 'utf-8'))
        LINE = 'REGISTER sip:' + SIP + ' SIP/2.0\r\nExpires: ' + OPCION + '\r\n'
        LINE += 'Authorization: Digest response= {}'.format(h.hexdigest())
        print("Enviando:", LINE, '\r\n')
        my_socket.send(bytes(LINE, 'utf-8') + b'\r\n')
        # METODO LOG --> SENT TO
        log(LINE,'snd')
        
        dato = my_socket.recv(1024)
        datos = dato.decode('utf-8').split()
        print("Recibido: ", dato.decode('utf-8'), '\r\n')
        # METODO LOG --> RECEIVED FROM
        log(dato.decode('utf-8'),'rcv')

# METODO LOG --> FINISHING
log('empty','finish')
print("Socket terminado.")
