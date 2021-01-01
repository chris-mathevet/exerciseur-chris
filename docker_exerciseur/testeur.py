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
from typing import Union

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
    else:
        image =  args.nom[0]
    éval = éprouve_dans_nouveau_container(image, code_etu, args.verbose)
    print(json.dumps(éval))

def trouve_image(docker_client, img):
    if isinstance(img, docker.models.images.Image):
        return img
    else:
        return docker_client.images.get(img)


def éprouve_dans_nouveau_container(
        exerciseur: Union[str, docker.models.images.Image],
        code_etu: Union[str, bytes],
        verbose=False,
        docker_client=None,
        docker_network='bridge'
    ):
    """
    Teste une tentative étudiante dans un nouveau container pour un exerciseur.

    @param exerciseur: l'exerciseur à utiliser, donné sous forme soit d'un identifiant d'image, soit d'un objet image de la bibliothèque docker
    @param code_etu: une chaîne de caractères contenant le code soumis par l'étudiant·e
    @param verbose: indique si on doit se répandre sur sys.stderr
    @param docker_client: un objet client-docker à réutiliser (None pour utiliser docker.from_env())
    @param docker_network: le réseau docker à utiliser

    @return le dictionnaire d'évaluation de la tentative (à sérialiser en json)
    """
    if isinstance(code_etu, bytes):
        code_etu = code_etu.decode()
    if verbose:
        print(sectionize("Code étudiant"), end="", file=sys.stderr)
        print(code_etu, end="", file=sys.stderr)
        print(sectionize("Fin code étudiant"), file=sys.stderr)

    docker_client = docker_client or docker.from_env()

    image = trouve_image(docker_client, exerciseur)
    lc = LogConfig(type=LogConfig.types.JSON, config={
        'max-size': '1g',
    })
    t_démarrage = time.perf_counter()
    container = docker_client.containers.run(image, detach=True, log_config=lc, network=docker_network, remove=True)
    if verbose:
        print("conteneur démarré en %.2f s" % (time.perf_counter() - t_démarrage), file=sys.stderr)
    container.reload()
    adresse_container = container.attrs['NetworkSettings']['Networks'][docker_network]['IPAddress']
    if verbose:
        print("conteneur en écoute sur", adresse_container, file=sys.stderr)
    t_début_réseau = time.perf_counter()
    délai_essais = 1
    socket_container = None
    while délai_essais < 1024 and not socket_container:
        try:
            socket_container = socket.create_connection((adresse_container, 5678))
        except ConnectionRefusedError:
            time.sleep(délai_essais * 0.001)
            délai_essais *= 2

    try:
        if verbose:
            print("connexion au conteneur ok", file=sys.stderr)

        socket_container.send(cbor.dumps(code_etu.encode('utf8')))
        délai_lecture = 1
        réponse = b''
        while délai_lecture < 1024 and len(réponse) == 0:
            réponse = socket_container.recv(4096)
            time.sleep(délai_lecture * 0.001)
            délai_lecture *= 2
        if verbose:
            print("temps réponse: %.2f s" % (time.perf_counter() - t_début_réseau), file=sys.stderr)
        d_réponse = json.loads(réponse)
        return d_réponse
    except Exception as e:
        return { "_valide": False, "_messages": ["Plantage du container", repr(e)],
                 "feedbacks_html": "<div>Plantage du container: " + repr(e) + "</div>"}
    finally:
        container.stop()
        if verbose:
            print(sectionize("logs du container"), file=sys.stderr)
            print(container.logs(since=datetime.datetime.min).decode(), file=sys.stderr)


def éprouve_dans_openfaas(
        id_exo: str,
        code_etu: Union[str, bytes],
        verbose=False
    ):
    """
    Teste une tentative étudiante dans un nouveau container pour un exerciseur.

    @param id_exo: l'ID de l'exerciseur (de la fonction openfaas qui sera appellée)
    @param code_etu: une chaîne de caractères contenant le code soumis par l'étudiant·e
    @param verbose: indique si on doit se répandre sur sys.stderr
    @param docker_client: un objet client-docker à réutiliser (None pour utiliser docker.from_env())
    @param docker_network: le réseau docker à utiliser

    @return le dictionnaire d'évaluation de la tentative (à sérialiser en json)
    """
    if isinstance(code_etu, bytes):
        code_etu = code_etu.decode()
    if verbose:
        print(sectionize("Code étudiant"), end="", file=sys.stderr)
        print(code_etu, end="", file=sys.stderr)
        print(sectionize("Fin code étudiant"), file=sys.stderr)

    #image = trouve_image(docker_client, exerciseur)
    lc = LogConfig(type=LogConfig.types.JSON, config={
        'max-size': '1g',
    })
    try:
        import requests
        réponse = requests.post('http://gateway:8080/function/%s'%id_exo[:62], data=cbor.dumps(code_etu.encode('utf8')))
        d_réponse = json.loads(réponse.text)
        return d_réponse
    except Exception as e:
        return { "_valide": False, "_messages": ["Plantage du container", repr(e)],
                 "feedbacks_html": "<div>Plantage du container: " + repr(e) + "</div>"}
