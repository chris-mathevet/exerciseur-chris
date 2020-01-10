#!/usr/bin/env python3

import cbor
import sys
import json
from socketserver import StreamRequestHandler, TCPServer
import signal
from {{module}} import {{NomClasse}}

class ServeurTentatives(StreamRequestHandler):

    def __init__(self, *args):
        self.ex = {{NomClasse}}()
        super().__init__(*args)
    
    def handle(self):
        code_etu = cbor.load(self.rfile)
        print("reçu: ", code_etu)
        réponse = self.ex.évalue(code_etu)
        self.wfile.write(json.dumps(réponse).encode() + b'\n')
        self.wfile.flush()

def sigterm_handler(_signo, _stack_frame):
    exit(0)

if __name__ == "__main__":
    port = 5678 if len(sys.argv) < 2 else int(sys.argv[1])
    signal.signal(signal.SIGTERM, sigterm_handler)
    with TCPServer(("", port), ServeurTentatives) as serv:
        serv.serve_forever()
