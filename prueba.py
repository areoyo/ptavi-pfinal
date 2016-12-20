#!/usr/bin/python3
# -*- coding: utf-8 -*-

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import sys
import smallsmilhandler
import json
import urllib.request


class karaokeLocal():
    def init(self, f):
        parser = make_parser()
        self.kHandler = clienthandler.ClientHandler()
        parser.setContentHandler(self.kHandler)
        parser.parse(f)
        self.data = self.kHandler.get_tags()s()

    def __str__(self):
        for atributos in self.data:
            tag = atributos['tag']
            line = str(tag+'\t')
            for atribute in atributos:
                if atributos != tag:
                    line = line+atribute+"="+atributos[atribute]+'\t'
            print(line)

    def to_json(self, filename):
        fichjson = open(filename.split('.')[0]+'.json', 'w')
        fichjson.write(json.dumps(self.data))
        fichjson.close()

    def do_local(self):
        for atributos in self.data:
            for atribute in atributos:
                if atributos[atribute][:7] == 'http://':
                    name = atributos[atribute].split('/')[-1]
                    url = urllib.request.urlretrieve(atributos[atribute], name)
                    atributos[atribute] = name

if __name__ == "__main__":
    """
    Programa principal
    """
    try:
        fich = open(sys.argv[1], 'r')
    except IndexError:
        sys.exit("Usage: python3 karaoke.py file.smil")

    karaoke = karaokeLocal()

    karaoke.init(fich)
    karaoke.__str__()
    karaoke.to_json(sys.argv[1])
    karaoke.do_local()
    karaoke.to_json('local')
    karaoke.__str__()
