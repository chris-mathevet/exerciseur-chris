#!/usr/bin/env python3
import cbor
import json
import argparse
import docker
from docker.types import LogConfig
import socket
import sys
import time
import datetime

parser = argparse.ArgumentParser(add_help=False)

parser.add_argument(
    "--dockerfile", help="l'image est à obtenir à partir d'un Dockerfile (désuet, utiliser plutôt la commande 'construit')"
)
parser.add_argument(
    "nom", help="le nom de l'image docker du testeur", nargs=1
)
parser.add_argument(
    "--fichier", help="l'image docker est à charger depuis un fichier",
    action="store_true"
)
parser.add_argument(
    "--code-etu", help="le code étudiant à soumettre"
)


epoch = datetime.datetime.fromtimestamp(0)

def sectionize(message):
    n = len(message)
    souligne = "\n" + n * "-" + "\n"
    return (souligne + message + souligne)

def main(args):
    if args.code_etu:
        with open(args.code_etu, 'rb') as f_etu:
            code_etu = f_etu.read()
    else:
        code_etu = b'tralala'

    if args.verbose:
        print(sectionize("Code étudiant"), end="")
        print(code_etu.decode(), end="")
        print(sectionize("Fin code étudiant"))
    
    docker_client = docker.from_env()
    
    image = docker_client.images.get(args.nom[0])
    if args.fichier:
        with open(args.nom[0], 'rb') as fichier_image:
            images = docker_client.images.load(fichier_image)
        assert len(images) == 1
        image = images[0]
    elif args.dockerfile:
        (image, log) = docker_client.images.build(path=args.nom[0])
        if args.verbose:
            print(sectionize("image construite, log de construction"))
            for line in log:
                print(json.dumps(line))
            print(sectionize("démarrage"))

    lc = LogConfig(type=LogConfig.types.JSON, config={
        'max-size': '1g',
    })
    t_démarrage = time.perf_counter()
    container = docker_client.containers.run(image, detach=True, log_config=lc, network_mode="bridge")
    if args.verbose:
        print("conteneur démarré en %.2f s" % (time.perf_counter() - t_démarrage))
    try:
        container.reload()
        adresse_container = container.attrs['NetworkSettings']['IPAddress']
        if args.verbose:
            print("conteneur en marche, sur", adresse_container)
        t_début_réseau = time.perf_counter()
        délai_essais = 1
        socket_container = None
        while délai_essais < 1024 and not socket_container:
            try:
                socket_container = socket.create_connection((adresse_container, 5678))
            except ConnectionRefusedError:
                time.sleep(délai_essais * 0.001)
                délai_essais *= 2
                

        if args.verbose:
            print("connexion au conteneur ok")

        socket_container.send(cbor.dumps(code_etu))
        délai_lecture = 1
        réponse = b''
        while délai_lecture < 1024 and len(réponse) == 0:
            réponse = socket_container.recv(4096)
            time.sleep(délai_lecture * 0.001)
            délai_lecture *= 2
        if args.verbose:
            print("temps réponse: %.2f s" % (time.perf_counter() - t_début_réseau))
        sys.stdout.write(réponse.decode())
    finally:
        container.stop()
        if args.verbose:
            print(sectionize("logs du container"))
            print(container.logs(since=datetime.datetime.min))
