#!/usr/bin/python3
# -*- coding: utf-8 -*-

from xml.sax import make_parser
from xml.sax.handler import ContentHandler


class UserAgentHandler(ContentHandler):

    def __init__(self):
        """
        Constructor. Inicializamos las variables
        """
        self.misdatos = {}
        self.attrs = {'account': ['username', 'passwd'],
                      'uaserver': ['ip', 'puerto'],
                      'rtpaudio': ['puerto'],
                      'regproxy': ['ip', 'puerto'],
                      'log': ['path'],
                      'audio': ['path'],
                      'server': ['name', 'ip', 'puerto'],
                      'database': ['path', 'passwdpath']}

    def startElement(self, name, atributes):
        """
        Método que se llama cuando se abre una etiqueta
        """
        if name in self.attrs:
            for atributo in self.attrs[name]:
                self.misdatos[name+'_'+atributo] = str(atributes.get(atributo, ""))

    def get_tags(self):
        """
        Método que se llama para guardar la lista de datos
        """
        return self.misdatos
