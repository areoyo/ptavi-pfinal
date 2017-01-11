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

print('DATOS DICCIONARIO:')
print(data)

SERVER = data["regproxy_ip"]
PORT = int(data["regproxy_puerto"])
SIP = data["account_username"]+':'+data["uaserver_puerto"]
fich_log = data["log_path"]
USER = data["account_username"]
AUD = data["audio_path"]
PORTRTP = data["rtpaudio_puerto"]

"""
FICHERO LOG
"""


def log(op, accion):
    fich = open(fich_log, 'a')
    hora = time.strftime('%Y%m%d%H%M%S', time.gmtime(time.time()))
    if op != 'empty':
        log_datos = str(SERVER) + ':' + str(PORT)
        if accion == 'snd':
            status = ' Sent to ' + log_datos + ' ' + op.replace('\r\n', ' ')
        elif accion == 'rcv':
            status = ' Received from ' + log_datos
            status += ' ' + op.replace('\r\n', ' ')
        elif accion == 'error':
            status = op
    else:
        if accion == 'start':
            status = ' Starting...'
        elif accion == 'finish':
            status = ' Finishing.'
        elif accion == 'error':
            status = ' Error: No proxy listening at '
            status += str(SERVER) + ' port ' + str(PORT)
    fich.write(hora + status + '\r\n')

"""
 COMIENZA CONEXION
"""


with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
    my_socket.connect((SERVER, PORT))
    try:
        log('empty', 'start')

        if METODO == 'REGISTER':
            LINE = 'REGISTER sip:{} SIP/2.0\r\nExpires: {}'.format(SIP, OPCION)
        elif METODO == 'INVITE':
            LINE = 'INVITE sip:{} SIP/2.0\r\n'.format(OPCION)
            LINE += 'Content-Type: application/sdp\r\n\r\n'
            LINE += 'v = 0\r\n'
            LINE += 'o = ' + data["account_username"] + ' '
            LINE += data['uaserver_ip'] + '\r\n'
            LINE += 's = MiSesion\r\n'
            LINE += 't = 0\r\n'
            LINE += 'm = audio {} RTP'.format(data['rtpaudio_puerto'])
        elif METODO == 'BYE':
            LINE = 'BYE sip:{} SIP/2.0'.format(OPCION)

        my_socket.send(bytes(LINE, 'utf-8') + b'\r\n')
        log(LINE, 'snd')

        dato = my_socket.recv(1024)
        datos = dato.decode('utf-8').split()
        log(dato.decode('utf-8'), 'rcv')
        print('RECIBIDO--:\r\n', dato.decode('utf-8'))
        if datos[1] == '100' and datos[7] == '180' and datos[13] == '200':
            METODO = 'ACK'
            LINE = METODO + " sip:" + datos[25] + " SIP/2.0"
            my_socket.send(bytes(LINE, 'utf-8') + b'\r\n')
            log(LINE, 'snd')
            aEjecutarVLC = 'cvlc rtp://@127.0.0.1:' + PORTRTP + '> /dev/null &'
            print("Vamos a ejecutar ", aEjecutarVLC)
           os.system(aEjecutarVLC)
            aEjecutar = "./mp32rtp -i " + datos[26] + " -p " + PORTRTP \
                        + " < " + AUD
            print("Vamos a ejecutar ", aEjecutar)
            os.system(aEjecutar)
            puerto = datos[17]
        elif datos[1] == '401':
            nonce = datos[7]
            h = hashlib.sha1()
            h.update(bytes(data["account_passwd"], 'utf-8'))
            h.update(bytes(nonce, 'utf-8'))
            LINE = 'REGISTER sip:' + SIP + ' SIP/2.0\r\nExpires: '
            LINE += OPCION + '\r\n'
            LINE += 'Authorization: Digest response= {}'.format(h.hexdigest())
            my_socket.send(bytes(LINE, 'utf-8') + b'\r\n')
            log(LINE, 'snd')

            dato = my_socket.recv(1024)
            datos = dato.decode('utf-8').split()
            log(dato.decode('utf-8'), 'rcv')
        elif datos[0] == 'ERROR':
            msg = 'Error: No server listening at ' + datos[-2] + ':'
            msg += datos[-1]
            log(msg, 'error')
            log('empty', 'finish')

        log('empty', 'finish')
        print("Socket terminado.")

    except ConnectionRefusedError:
        log('empty', 'error')
        log('empty', 'finish')
        print("Socket terminado.")
