#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import socketserver
import socket
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import useragenthandler
import hashlib
import time
import json

"""
 COMPROBACION DE LA ENTRADA
"""
if len(sys.argv) != 2:
    sys.exit("Usage: python3 proxy_registrar.py config")
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

SERVER = data["server_ip"]
PORT = int(data["server_puerto"])
fich = open(data['database_passwdpath'], 'r')
lineas = fich.readlines()
nonce = '654578'
fich_log = data["log_path"]
log_datos = str(SERVER) + ':' + str(PORT)

"""
FICHERO LOG
"""


def log(opcion, accion):
    fich = open(fich_log, 'a')
    hora = time.strftime('%Y%m%d%H%M%S', time.gmtime(time.time()))
    if opcion != 'empty':
        if accion == 'snd':
            status = ' Sent to ' + log_datos + ' '
            status += opcion.replace('\r\n', ' ')
        elif accion == 'rcv':
            status = ' Received from ' + log_datos + ' '
            status += opcion.replace('\r\n', ' ')
        elif accion == 'error':
            portfail = opcion.split()[-1]
            IPfail = opcion.split()[-2]
            status = ' Error: No server listening at '
            status += str(IPfail) + ' port ' + str(portfail)
    else:
        if accion == 'start':
            status = ' Starting...'
        elif accion == 'finish':
            status = ' Finishing.'
    fich.write(hora + status + '\r\n')

"""
 BASE DE DATOS DE USUARIOS REGISTRADOS
"""


class RegisterHandler(socketserver.DatagramRequestHandler):

    misdatos = {}

    """
    CREO FICHERO DE REGISTRO y escribo
    """
    def register2json(self):
        json.dump(self.misdatos, open(data['database_path'], 'w'))

    """
    COMPRUEBA SI HAY FICHERO, LEE SU CONTENIDO Y LO USA DE LISTA DE USUARIO
    """
    def json2registered(self):
        try:
            with open(data['database_path']) as client_file:
                self.misdatos = json.load(client_file)
        except:
            self.register2json()

    """
    CUANDO PASA EL TIEMPO DE EXPIRACION --> BORRO CLIENTE
    """
    def delete(self):
        tmpList = []
        for cliente in self.misdatos:
            expires = int(self.misdatos[cliente][-1])
            if expires < time.time():
                tmpList.append(cliente)
        for client in tmpList:
            del self.misdatos[client]

    def register(self, t_register, user_register, address_c, puerto):
        self.json2registered()
        self.hora = float(time.time())
        self.h_ex = float(time.time()) + float(t_register)
        self.datoscliente = [address_c, puerto, self.hora, self.h_ex]
        self.misdatos[user_register] = self.datoscliente
        if int(t_register) == 0:
            del self.misdatos[user_register]
        self.wfile.write(b"SIP/2.0 200 OK\r\n")
        self.delete()
        self.register2json()

    def handle(self):
        self.json2registered()
        # Escribe dirección y puerto del cliente (de tupla client_address)
        while 1:
            log('empty', 'start')
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read()
            datos = line.decode('utf-8').split()
            print('RECIBIDO --:\r\n', line.decode('utf-8'))
            # Si no hay más líneas salimos del bucle infinito
            if not line:
                break

            self.json2registered()
            log(line.decode('utf-8'), 'rcv')

            """
             CODIGOS DE RESPUESTA
            """
            if datos[0] == 'REGISTER':
                if 'Authorization:' in datos:
                    response = datos[-1]
                    user = datos[1].split(':')[1]
                    port = datos[1].split(':')[-1]
                    for linea in lineas:
                        if linea.split()[0] == user:
                            dat_passwd = linea.split()[-1]
                            h = hashlib.sha1()
                            h.update(bytes(dat_passwd, 'utf-8'))
                            h.update(bytes(nonce, 'utf-8'))
                            dat_nonce = h.hexdigest()
                            if dat_nonce == response:
                                c_reg = datos[1].split(':')[1]
                                address = self.client_address[0]
                                self.register(datos[4], c_reg, address, port)
                                msg = "SIP/2.0 200 OK\r\n"
                            else:
                                msg = "SIP/2.0 404 User Not Found\r\n"
                            self.wfile.write(bytes(msg, 'utf-8'))
                            log(msg, 'snd')
                else:
                    msg = "SIP/2.0 401 Unauthorized\r\n"
                    msg += "WWW Authenticate: Digest nonce= " + nonce + '\r\n'
                    self.wfile.write(bytes(msg, 'utf-8'))
                    log(msg, 'snd')
            elif datos[0] == "INVITE" or "ACK" or "BYE":
                self.json2registered()
                user = datos[1].split(':')[1]
                if user in self.misdatos.keys():
                    newport = int(self.misdatos[user][1])
                    newIP = self.misdatos[user][0]
                    newsend = line.decode('utf-8').split('\r\n')
                    newline = newsend[0]
                    newline += '\r\nVia: SIP/2.0/UDP ' + log_datos + '\r\n'
                    if datos[0] == 'INVITE':
                        newline += newsend[1] + '\r\n\r\n'
                        newline += newsend[3] + '\r\n'
                        newline += newsend[4] + '\r\n' + newsend[5] + '\r\n'
                        newline += newsend[6] + '\r\n' + newsend[7] + '\r\n'
                    try:
                        s_skt= socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
                        with s_skt as my_socket:
                            my_socket.setsockopt(socket.SOL_SOCKET,
                                                 socket.SO_REUSEADDR, 1)
                            my_socket.connect((newIP, newport))
                            my_socket.send(bytes(newline, 'utf-8'))
                            log(newline, 'snd')
                            if datos[0] != 'ACK':
                                datonew = my_socket.recv(1024)
                                log(datonew.decode('utf-8'), 'rcv')
                                print('RECIBIDO:\r\n', datonew.decode('utf-8'))
                                newsend = datonew.decode('utf-8').split('\r\n')
                                newrsp = newsend[0] + '\r\nVia: SIP/2.0/UDP '
                                newrsp += log_datos + '\r\n'
                                if datos[0] == 'INVITE':
                                    newrsp += '\r\n' + newsend[2]
                                    newrsp += '\r\nVia: SIP/2.0/UDP '
                                    newrsp += log_datos + '\r\n\r\n'
                                    newrsp += newsend[4]
                                    newrsp += '\r\nVia: SIP/2.0/UDP '
                                    newrsp += log_datos + '\r\n' + newsend[5]
                                    newrsp += '\r\n\r\n' + newsend[6] + '\r\n'
                                    newrsp += newsend[7] + '\r\n' + newsend[8]
                                    newrsp += '\r\n' + newsend[9] + '\r\n'
                                    newrsp += newsend[10] + '\r\n'
                                self.wfile.write(bytes(newrsp, 'utf-8'))
                                log(newrsp, 'snd')
                    except ConnectionRefusedError:
                        msg = 'ERROR {} {}'.format(newIP, newport)
                        self.wfile.write(bytes(msg, 'utf-8'))
                        log(msg, 'error')
                        log(msg, 'snd')
                else:
                    msg = "SIP/2.0 404 User Not Found\r\n"
                    self.wfile.write(bytes(msg, 'utf-8'))
                    log(msg, 'snd')
            elif datos[0] != "INVITE" or "BYE" or "ACK":
                LINE = "SIP/2.0 405 Method Not Allowed\r\n"
                self.wfile.write(bytes(LINE, 'utf-8'))
                log(LINE, 'snd')
            else:
                LINE = "SIP/2.0 400 Bad Request\r\n"
                self.wfile.write(bytes(LINE, 'utf-8'))
                log(LINE, 'snd')

if __name__ == "__main__":
    serv = socketserver.UDPServer((SERVER, PORT), RegisterHandler)
    print('Server MiServidorBigBang listening at port 5555...\r\n')
    try:
        serv.serve_forever()

    except KeyboardInterrupt:
        print("Finalizado servidor")
        log('empty', 'finish')
