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

print('DATOS DICCIONARIO:') ##
print(data) ##

SERVER = data["server_ip"]
PORT = int(data["server_puerto"])
fich = open(data['database_passwdpath'], 'r')
lineas = fich.readlines()
nonce = '654578'
fich_log = data["log_path"]

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
        fich.write(hora  + status + '\r\n')

"""
 BASE DE DATOS DE USUARIOS REGISTRADOS
"""
class RegisterHandler(socketserver.DatagramRequestHandler):

    misdatos= {}
    
    """
    CREO FICHERO DE REGISTRO y escribo
    """
    def register2json(self):
        json.dump(self.misdatos, open(data['database_path'], 'w'))
        
    """
    COMPRUEBA SI HAY FICHERO, LEE SU CONTENIDO Y LO USA LISTA DE USUARIO
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
            print ('DELETE', client) 
            
    def register (self, t_register, user_register, address_c, puerto):
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
        # Escribe dirección y puerto del cliente (de tupla client_address)
        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read()
            datos = line.decode('utf-8').split()
            # Si no hay más líneas salimos del bucle infinito
            if not line:
                break
            
            log('empty','start')
            log(line.decode('utf-8'),'rcv')
            
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
                                client_register = datos[1].split(':')[1]
                                self.register (datos[4], client_register, \
                                               self.client_address[0], port)
                            else:
                                msg = "SIP/2.0 404 User Not Found\r\n"
                                self.wfile.write(bytes(msg, 'utf-8'))
                                log(msg,'snd')
                else:
                    msg = "SIP/2.0 401 Unauthorized\r\n"
                    msg += "WWW Authenticate: Digest nonce= " + nonce + '\r\n'
                    self.wfile.write(bytes(msg, 'utf-8'))
                    log(msg,'snd')
                                        
            elif datos[0] == "INVITE" or "ACK" or "BYE":
                self.json2registered()
                user = datos[1].split(':')[1]
                if user in self.misdatos.keys():
                    newport = int(self.misdatos[user][1])
                    newIP = self.misdatos[user][0]
                    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) \
                        as my_socket:
                        my_socket.setsockopt(socket.SOL_SOCKET, 
                                             socket.SO_REUSEADDR, 1)
                        my_socket.connect((newIP, newport))
                        my_socket.send(line)
                        log(line.decode('utf-8'),'snd')
                        if datos [0] != 'ACK':
                            datonew = my_socket.recv(1024)
                            log(datonew.decode('utf-8'),'rcv')
                            self.wfile.write(datonew)
                            log(datonew.decode('utf-8'),'snd')
                else:
                    msg = "SIP/2.0 404 User Not Found\r\n"
                    self.wfile.write(bytes(msg, 'utf-8'))
                    log(msg,'snd')
                
            elif datos[0] != "INVITE" or "BYE" or "ACK":
                LINE = "SIP/2.0 405 Method Not Allowed\r\n"
                self.wfile.write(bytes(LINE, 'utf-8'))
                log(LINE,'snd')
            else:
                LINE = "SIP/2.0 400 Bad Request\r\n"
                self.wfile.write(bytes(LINE, 'utf-8'))
                log(LINE,'snd')

if __name__ == "__main__":
    serv = socketserver.UDPServer((SERVER, PORT), RegisterHandler)
    print('Server MiServidorBigBang listening at port 5555...\r\n')
    try:
        serv.serve_forever()
        
    except KeyboardInterrupt:
        print("Finalizado servidor")
        log('empty','finish')
