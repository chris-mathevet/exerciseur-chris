import cbor
import sys
import json
from socketserver import StreamRequestHandler, TCPServer

"""
Un serveur pour répondre à une tentative étudiante
On est content quoi qu'on nous propose…
"""

class ToujoursContent(StreamRequestHandler):

    def handle(self):
        code_etu = cbor.load(self.rfile)
        self.wfile.write(json.dumps({"résultat": "fantastique"}).encode())
        self.wfile.flush()

if __name__ == "__main__":
    port = 5678 if len(sys.argv) < 2 else int(sys.argv[1])
    with TCPServer(("", port), ToujoursContent) as serv:
       serv.serve_forever()

