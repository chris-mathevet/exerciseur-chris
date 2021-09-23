import os
import sys
import argparse
import json
import tempfile

from .exerciseur import Exerciseur

parser = argparse.ArgumentParser(add_help=False)

parser.add_argument(
    "dossier", help="Le dossier contenant les sources de l'exerciseur",
    nargs='?'
)
parser.add_argument(
    "--type", help="Le type d'exerciseur à construire (par défaut, %(default)s)",
    choices=Exerciseur.types_exerciseurs,
    default="DémonPython"
)
parser.add_argument(
    "--classe", help="la classe exerciseur, pour les exerciseurs type PackagePython"
)
parser.add_argument(
    "--module", help="le module de tests de l'exerciseur"
)
parser.add_argument(
    "--sans-openfaas", help="ne pas utiliser openfaas", action="store_true"
)
parser.add_argument(
    "--prépare", help="ne construit pas l'image docker, mais crée seulement le répertoire avec un Dockerfile pour docker build",
    action="store_true"
)

parser.add_argument("--package", dest="cbor_out_file", help="créer un paquet cbor des sources dans un fichier",
    type=argparse.FileType('wb'),
)

def main(args):
    dossier_source = args.dossier or "."
    métadonnées={}
    if args.classe:
        métadonnées['nom_classe'] = args.classe
    if args.module:
        if args.type == 'Jacadi':
            métadonnées['fichier_ens'] = args.module
        else:
            métadonnées['nom_module'] = args.module
    if args.prépare:
        chemin = prépare_exerciseur(args.type, dossier_source, args.verbose, **métadonnées)
        print(chemin)
    if args.cbor_out_file:
        debug_out = args.verbose and sys.stderr
        dossier_source = os.path.abspath(dossier_source)
        with tempfile.TemporaryDirectory() as rép_travail:
            ex = Exerciseur.avec_type(dossier_source, args.type, debug_out=debug_out)
            ex.utiliser_rép_travail(rép_travail + '/src')
            ex.copie_source()
            ex.prépare_source()
            ex.écrit_dockerfile()
            paquet = ex.empaquète().vers_cbor()

    else:
        id_image = construit_exerciseur(args.type, dossier_source, args.verbose,
                                        cbor_out=args.cbor_out_file, avec_openfaas=(not args.sans_openfaas),
                                        **métadonnées)
        print(id_image.split(':')[1])


def construit_exerciseur(type_ex, dossier_source, verbose, cbor_out=None, avec_openfaas=True, **kwargs):
    """
    Construit un exerciseur. Les arguments correspondent à ceux de `docker-exerciseur construit`

    @param type_ex: le type d'exerciseur, parmi "DémonPy", "PackagePy", "TestsPy", "Dockerfile" ou "Jacadi"
    @param dossier_source: le chemin des sources de l'exerciseur
    @param verbose: un booléen, vrai pour afficher plus d'informations sur sys.stderr
    @param kwarg: un dictionnaire qui sert à donner des arguments supplémentaires en fonction de `type_ex`.
    - pour PackagePy, `nom_module="tralala"` indique quel module contient la classe exerciseur et `nom_classe="NomClasse"` le nom de cette classe
    - pour TestsPython, `nom_module="tralala"` indique quel module contient les tests
    - pour Jacadi, `module="mod_ens"` indique quel module contient le code enseignant.

    @return l'idententifiant de l'image construite pour cet exerciseur.
    """
    debug_out = verbose and sys.stderr
    dossier_source = os.path.abspath(dossier_source)
    ex = Exerciseur.avec_type(dossier_source, type_ex, debug_out=debug_out, avec_openfaas=avec_openfaas, **kwargs)
    res =  ex.construire()
    if debug_out:
        print("Exercice:", dossier_source, file=debug_out)
        print(ex.métadonnées(), file=debug_out)
    return res

def prépare_exerciseur(type_ex, dossier_source, verbose, **kwargs):
    """
    Construit un exerciseur. Les arguments correspondent à ceux de `docker-exerciseur construit`

    @param type_ex: le type d'exerciseur, parmi "DémonPy", "PackagePy", "TestsPy", "Dockerfile" ou "Jacadi"
    @param dossier_source: le chemin des sources de l'exerciseur
    @param verbose: un booléen, vrai pour afficher plus d'informations sur sys.stderr
    @param kwarg: un dictionnaire qui sert à donner des arguments supplémentaires en fonction de `type_ex`.
    - pour PackagePy, `nom_module="tralala"` indique quel module contient la classe exerciseur et `nom_classe="NomClasse"` le nom de cette classe
    - pour TestsPython, `nom_module="tralala"` indique quel module contient les tests
    - pour Jacadi, `module="mod_ens"` indique quel module contient le code enseignant.

    @return l'idententifiant de l'image construite pour cet exerciseur.
    """
    debug_out = verbose and sys.stderr
    dossier_source = os.path.abspath(dossier_source)
    ex = Exerciseur.avec_type(dossier_source, type_ex, debug_out=debug_out, **kwargs)
    import tempfile
    td = tempfile.mkdtemp()
    ex.utiliser_rép_travail(td + '/src')
    ex.copie_source()
    ex.prépare_source()
    ex.écrit_dockerfile()
    if verbose:
        print("métadonnées:", ex.métadonnées(), file=debug_out)
    return td
