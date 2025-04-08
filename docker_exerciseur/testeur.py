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
import requests
from typing import Union
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

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

parser.add_argument(
    "--verbose", help="permet d'afficher des informations sur l'éxécution du programme",
    action="store_true"
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
    éval = éprouve_dans_nouveau_container(image, code_etu, args.verbose )
    print(json.dumps(éval))

def trouve_image(docker_client, img):
    if isinstance(img, docker.models.images.Image):
        return img
    else:
        return docker_client.images.get(img)


def éprouve_dans_nouveau_container(
        exerciseur: Union[str, docker.models.images.Image],
        code_etu: Union[str, bytes],
        verbose=True,
        docker_client=None,
        docker_network='bridge',
        **kwargs
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
    retry_strategy = Retry(
        total=5,
        backoff_factor=0.1,
        status_forcelist=[429, 500, 502, 503, 504],
        # method_whitelist=["HEAD", "GET", "OPTIONS"] # Plus supporté 
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("http://", adapter)

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
    dict_code_etu = {"code_etu": code_etu.encode('utf8')}
    dict_code_etu.update(kwargs)
    payload = cbor.dumps(dict_code_etu)
    taille = "{:x}".format(len(payload))
    msg = taille.encode() + b"\n" + payload + b"\n0\n"
    if verbose:
        print("envoi de: {}".format(msg), file=sys.stderr)
    try:
        print(sectionize("Envoie"),file=sys.stderr)
        url_container = "http://" + adresse_container + ":8082/"
        print("URL :",  url_container, file=sys.stderr)
        réponse = http.post(url_container, data=msg)
        if verbose:
            print("temps réponse: %.2f s" % (time.perf_counter() - t_début_réseau), file=sys.stderr)
        d_réponse = json.loads(réponse.text)
        return d_réponse
    except json.JSONDecodeError as e:
        return {  "_valide": False, "_messages": ["Plantage du container, impossible de parser", e.doc],
                 "feedbacks_html": "<div>Plantage du container: impossible de parser " + e.doc + "</div>"}
    except Exception as e:
        return { "url": url_container, "_valide": False, "_messages": ["Plantage du container", repr(e)],
                 "feedbacks_html": "<div>Plantage du container: " + repr(e) + "</div>"}
    finally:
        if verbose:
            print(sectionize("logs du container"), file=sys.stderr)
            print(container.logs(since=datetime.datetime.min).decode(), file=sys.stderr)
            print(sectionize("Fin logs du container"), file=sys.stderr)
        # container.stop() 
                


def éprouve_dans_openfaas(
        id_exo: str,
        code_etu: Union[str, bytes],
        verbose=False,
        **kwargs
    ):
    """
    Teste une tentative étudiante dans un nouveau container pour un exerciseur.

    @param id_exo: l'ID de l'exerciseur (de la fonction openfaas qui sera appellée)
    @param code_etu: une chaîne de caractères contenant le code soumis par l'étudiant·e
    @param verbose: indique si on doit se répandre sur sys.stderr
    @param kwargs: arguments supplémentaires à passer à la fonction de test
    @return le dictionnaire d'évaluation de la tentative (à sérialiser en json)
    """
    if isinstance(code_etu, bytes):
        code_etu = code_etu.decode()
    if verbose:
        print(sectionize("Code étudiant"), end="", file=sys.stderr)
        print(code_etu, end="", file=sys.stderr)
        print(sectionize("Fin code étudiant"), file=sys.stderr)

    lc = LogConfig(type=LogConfig.types.JSON, config={
        'max-size': '1g',
    })
    try:
        dict_code_etu = {"code_etu": code_etu.encode('utf8')}
        dict_code_etu.update(kwargs)
        réponse = requests.post('http://gateway:8080/function/%s'%id_exo[:62], data=cbor.dumps(dict_code_etu))
        d_réponse = json.loads(réponse.text)
        return d_réponse
    except json.JSONDecodeError as e:
        return { "_valide": False, "_messages": ["Plantage du container, impossible de parser", e.doc],
                 "feedbacks_html": "<div>Plantage du container: impossible de parser " + e.doc + "</div>"}
    except Exception as e:
        return { "_valide": False, "_messages": ["Plantage du container", repr(e)],
                 "feedbacks_html": "<div>Plantage du container: " + repr(e) + "</div>"}
