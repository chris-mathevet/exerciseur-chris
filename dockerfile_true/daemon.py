import cbor
import sys
import json
from socketserver import StreamRequestHandler, TCPServer

"""
Un serveur pour répondre à une tentative étudiante
On est content quoi qu'on nous propose…

"""

# def serve(port):
#     sock = 

class ToujoursContent(StreamRequestHandler):

    def handle(self):
        code_etu = cbor.load(self.rfile)
        print(code_etu)
        self.wfile.write(json.dumps({"résultat": "fantastique"}).encode())
        self.wfile.close()
        
if __name__ == "__main__":
    port = 5678 if len(sys.argv) < 2 else int(sys.argv[1])

    with TCPServer(("localhost", port), ToujoursContent) as serv:
        serv.serve_forever()
            
                         
