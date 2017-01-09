#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import socketserver
import os
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
print('Server MiServidorBigBang listening at port 5555...\r\n')

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
base_datos = open(data['database_path'], 'r')
base = base_datos.readLines()
lineas = fich.readlines()
nonce = '654578'

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
            with base_datos as client_file:
                self.misdatos = json.load (client_file)
        except:
            self.register2json()
   
    """
    CUANDO PASA EL TIEMPO DE EXPIRACION --> BORRO CLIENTE
    """ 
    def delete(self):
        tmpList = []
        for cliente in self.misdatos:
            hora_e = int(self.misdatos[cliente][-1])
            hora = time.time()
            if hora_e < hora:
                tmpList.append(cliente)
            for client in tmpList:
                del self.misdatos[client]

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
            
            # METODO LOG --> STARTING
            # METODO LOG --> RECEIVED FROM 
            """
             CODIGOS DE RESPUESTA
            """                
            if datos[0] == 'REGISTER':
                if datos[5] == 'Authorization:':
                    response = datos[-1]                 
                    user = datos[1].split(':')[1]
                    port = datos[1].split(':')[-1]
                    for line in lineas:
                        if line.split()[0] == user:
                            dat_passwd = line.split()[-1]
                            h = hashlib.sha1()
                            h.update(bytes(dat_passwd, 'utf-8'))
                            h.update(bytes(nonce, 'utf-8'))
                            dat_nonce = h.hexdigest()
                            if dat_nonce == response:
                                register = True
                                print ('REGISTRO USUARIO')
                        else:
                            register = False
                            
                    if register == True:
                        self.json2registered()
                        self.hora = float(time.time()) + float(datos[4])                                                     
                        self.datoscliente = [self.client_address[0], port, \
                                             time.time(), self.hora]
                        self.misdatos[user] = self.datoscliente
                        if int(datos[4]) == 0:
                            del self.misdatos[datos[1].split(':')[4]] 
                        self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
                        self.delete()
                        self.register2json()
                        
                        print (self.misdatos)
                        
                    elif register == False:
                        self.wfile.write(b"SIP/2.0 404 User Not Found\r\n")

                else:
                    self.wfile.write(b"SIP/2.0 401 Unauthorized\r\n")
                    self.wfile.write(b'WWW Authenticare: Digest nonce: ' + \
                                     bytes(nonce, 'utf-8') + b'\r\n')
                    # METODO LOG --> SENT TO
                                        
            elif datos[0] == "INVITE" or "ACK" or "BYE":
                user = datos[1].split(':')[1]
                for line in lineas:
                    if user in self.misdatos.keys():
                        newport = int(self.misdatos[user][1])
                        newIP = self.misdatos[user][0]
                        print(user, newport, newIP)
                        #misdatos[line] == user:
                        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) \
                            as my_socket:
                            my_socket.setsockopt(socket.SOL_SOCKET,
                                                 socket.SO_REUSEADDR, 1) ##
                            my_socket.connect((newIP, newport))
                            
                            print("Enviando:", LINE, '\r\n')
                            my_socket.send(bytes(line, 'utf-8') + b'\r\n') ##
                            # METODO LOG  --> SENT TO
                            
                            dato = my_socket.recv(1024)
                            datos = dato.decode('utf-8').split() ##
                            print("Recibido: ", dato.decode('utf-8'), '\r\n') ##
                            # METODO LOG --> RECEIVED FROM
                        self.wfile.write(dato)
                        # METODO LOG --> SENT TO
                    else:
                        self.wfile.write(b"SIP/2.0 404 User Not Found\r\n")
                        # METODO LOG --> SENT TO
            elif datos[0] != "INVITE" or "BYE" or "ACK":
                self.wfile.write(b"SIP/2.0 405 Method Not Allowed\r\n") 
            else:
                self.wfile.write(b"SIP/2.0 400 Bad Request\r\n")

if __name__ == "__main__":
    serv = socketserver.UDPServer((SERVER, PORT), RegisterHandler)
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")
        # METODO LOG --> FINISHING
