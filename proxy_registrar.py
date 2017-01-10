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
    print('LOG') ##
    fich = open (fich_log, 'a')
    hora = time.strftime('%Y%m%d%H%M%S', time.gmtime(time.time()))
    if opcion != 'empty':
        if accion == 'snd':
            status = ' Sent to '
        elif accion == 'rcv':
            status = ' Received from '
        fich.write(hora + status + opcion.replace('\r\n',' ') + '\r\n')
    else:
        if accion == 'start':
            status = ' Starting...'
        elif accion == 'finish':
            status = ' Finishing.'  
        elif accion == 'error':
            status ==' Error: No server listening at '+SERVER+ ' port ' + PORT
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
            hora = time.time()
            if expires < hora:
                tmpList.append(cliente)
                expire_t = True
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
                    for line in lineas:
                        if line.split()[0] == user:
                            dat_passwd = line.split()[-1]
                            h = hashlib.sha1()
                            h.update(bytes(dat_passwd, 'utf-8'))
                            h.update(bytes(nonce, 'utf-8'))
                            dat_nonce = h.hexdigest()
                            if dat_nonce == response:
                                self.json2registered()
                                self.hora = float(time.time())
                                self.h_ex = float(time.time()) + float(datos[4])                                                
                                self.datoscliente = [self.client_address[0], \
                                                    port, self.hora, \
                                                    self.h_ex]
                                self.misdatos[user] = self.datoscliente
                                if int(datos[4]) == 0:
                                    del self.misdatos[datos[1].split(':')[1]] 
                                self.wfile.write(b"SIP/2.0 200 OK\r\n")
                                self.delete()
                                self.register2json()                   
                                print ('DESPUES DE DEL', self.misdatos) ##
                            else:
                                msg = "SIP/2.0 404 User Not Found\r\n"
                                self.wfile.write(bytes(msg, 'utf-8'))
                                log(msg,'snd')

                else:
                    msg = "SIP/2.0 404 User Not Found\r\n"
                    msg += "WWW Authenticate: Digest nonce: " + nonce + '\r\n'
                    self.wfile.write(bytes(msg, 'utf-8'))
                    log(msg,'snd')
                                        
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
                            
                            datonew = my_socket.recv(1024)
                            datos = datonew.decode('utf-8').split() ##
                            print("Recibido: ", dato.decode('utf-8'), '\r\n') ##
                            # METODO LOG --> RECEIVED FROM
                        self.wfile.write(datonew)
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
