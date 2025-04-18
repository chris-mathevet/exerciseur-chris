"""
Un serveur pour répondre à une tentative étudiante
On est content quoi qu'on nous propose…
"""

import cbor
import sys
import json
import signal
from http.server import BaseHTTPRequestHandler
import socketserver


def résultat(code_etu):
    return {
        "_valide": True,
        "_messages": ["T'es un·e champion·ne", "C'est exactement '" + str(code_etu) + "' que j'attendais"],
        'feedbacks_html': "<div>\n<p>Exercice réussi!</p>\n<ul>\n<li>T'es un·e champion·ne</li>\n<li>C'est exactement 'b'coucou'' que j'attendais</li>\n</ul>\n</div>\n"
    }


class Handler(BaseHTTPRequestHandler):

    def do_POST(self):
        mesg=b""
        while True:
            line = self.rfile.readline().strip()
            chunk_length = int(line, 16)
            if chunk_length != 0:
                    chunk = self.rfile.read(chunk_length)
                    mesg+=chunk
                    self.rfile.readline()
            else:
                break


        self.send_response(200)
        self.end_headers()        
        dict_code_etu = cbor.loads(mesg)
        code_etu = dict_code_etu["code_etu"]
        self.wfile.write(json.dumps(résultat(code_etu)).encode() + b'\n')
        self.wfile.flush()

def sigterm_handler(_signo, _stack_frame):
    exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, sigterm_handler)
    # with socketserver.TCPServer(("", 8082), Handler ) as httpd: # Sans OpenFaas
    with socketserver.TCPServer(("", 8080), Handler ) as httpd: # Avec OpenFaas
        httpd.serve_forever()
