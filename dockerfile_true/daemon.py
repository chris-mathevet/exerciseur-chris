import cbor
import sys
import json
from socketserver import StreamRequestHandler, TCPServer
import signal
import system

"""
Un serveur pour répondre à une tentative étudiante
On est content quoi qu'on nous propose…
"""

def résultat(code_etu):
    return {
        "_valide": True,
        "_messages": ["T'es un champion", "C'est exactement '" + str(code_etu) + "' que j'attendais"],
        "_temps": "0ms"
    }

class ToujoursContent(StreamRequestHandler):

    def handle(self):
        code_etu = cbor.load(self.rfile)
        print("reçu: ", code_etu)
        self.wfile.write(json.dumps(résultat(code_etu)).encode() + b'\n')
        self.wfile.flush()

if __name__ == "__main__":
    port = 5678 if len(sys.argv) < 2 else int(sys.argv[1])
    with TCPServer(("", port), ToujoursContent) as serv:
        serv.serve_forever()
