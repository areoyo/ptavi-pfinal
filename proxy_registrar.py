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
                
            """
             CODIGOS DE RESPUESTA
            """                
            if datos[0] == 'REGISTER':
                self.wfile.write(b"SIP/2.0 401 Unauthorized\r\n")
                if datos[5] == 'Authorization':
                    self.wfile.write(b"SIP/2.0 200 OK" + b"\r\n")
                else:
                    self.wfile.write(b'WWW Authenticare: Digest nonce:"45"\r\n')
            elif datos[0] == "INVITE":
                self.wfile.write(b"SIP/2.0 100 Trying" + b"\r\n")
                self.wfile.write(b"SIP/2.0 180 Ring" + b"\r\n")
                LINE = 'SIP/2.0 200 OK\r\n'
                LINE += 'Content-Type: application/sdp' + '\r\n\r\n' 
                LINE += 'v = 0\r\n' 
                LINE += 'o = {} {}\r\n'.format(data["account_username"], data['uaserver_ip'])
                LINE += 's = MiSesion\r\n'
                LINE += 't = 0\r\n'
                LINE += 'm = audio {} RTP\r\n'.format(data['rtpaudio_puerto'])
                self.wfile.write(bytes(LINE,'utf-8'))
            elif datos[0] == "ACK":
                aEjecutar = "./mp32rtp -i " + IP + " -p 23032 < " + FICH
                print("Vamos a ejecutar ", aEjecutar)
                os.system(aEjecutar)
            elif datos[0] == "BYE":
                self.wfile.write(b"\r\n" + b"SIP/2.0 200 OK" + b"\r\n")
            elif datos[0] != "INVITE" or "BYE" or "ACK":
                self.wfile.write(b"SIP/2.0 405 Method Not Allowed" + b"\r\n")
            else:
                self.wfile.write(b"SIP/2.0 400 Bad Request" + b"\r\n")

"""
 BASE DE DATOS DE USUARIOS REGISTRADOS
"""
class RegisterHandler(socketserver.DatagramRequestHandler):

    misdatos= {}
    
    """
    CREO FICHERO DE REGISTRO
    """
    def register2json(self):
        json.dump(self.misdatos, open('registered.json', 'w'))
    
    def json2registered(self):
        try:
            with open('registered.json') as client_file:
                self.misdatos = json.load (client_file)
        except:
            self.register2json()
    
    def time_out(self):
        cliente = []
        for client in self.misdatos:
            time_expires = self.misdatos[client]['expires']
            time_expire = time.strptime(time_expires, '%Y-%m-%d %H:%M:%S')
            if time_expire <= time.gmtime(time.time()):
                cliente.append(client)
        for hora in cliente:
            del self.misdatos[hora]
                 
    def handle(self):        
        datos = self.rfile.read().decode('utf-8').split()
        if datos[0] == 'REGISTER':
            self.hora = float(time.time()) + float(datos[-1])            
            self.expires = time.strftime('%Y-%m-%d %H:%M:%S', 
                                         time.gmtime(self.hora))
            self.datoscliente = {'address': self.client_address[0], 'expires': self.expires}
            self.misdatos[datos[1].split(':')[-1]] = self.datoscliente
            if int(datos[-1]) == 0:
                del self.misdatos[datos[1].split(':')[-1]]     
        self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
        self.time_out()
        self.register2json()
        print (self.misdatos)


if __name__ == "__main__":
    serv = socketserver.UDPServer((SERVER, PORT), EchoHandler)
    print("Listening...")
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")
