import docker
import io
import tempfile
import os
import sys
import shutil
import argparse
import importlib
import tarfile
from pkg_resources import resource_string

from .exerciseur import Exerciseur

parser = argparse.ArgumentParser(add_help=False)
        
def main(args):
    if args.source:
        if args.source and os.path.isfile(args.source):
            source = FluxTar(open(args.source, 'rb'))
        else:
            assert os.path.isdir(args.source)
            source = DossierSource(args.source)
    else:
        source = DossierSource('.')
    id_img = construit_exerciseur(args.type, source, args.verbose, classe=args.classe, module=args.module )
    print(id_img)


def construit_exerciseur(type_ex, source, verbose, **kwargs):
    """
    Construit un exerciseur. Les arguments correspondent à ceux de `docker-exerciseur construit`

    @param type_ex: le type d'exerciseur, parmi "DémonPy", "PackagePy", "TestsPy", "Dockerfile" ou "Jacadi"
    @param source: les sources de l'exerciseur, le dossier contenant soit un `FluxTar`, soit un `DossierSource`
    @param verbose: un booléen, vrai pour afficher plus d'informations sur sys.stderr
    @param kwarg: un dictionnaire qui sert à donner des arguments supplémentaires en fonction de `type_ex`.
    - pour PackagePy, `module="nom_module"` indique quel module contient la classe exerciseur et `classe="NomClasse"` le nom de cette classe
    - pour TestsPy, `module="nom_module"` indique quel module contient les tests
    - pour Jacadi, `module="mod_ens"` indique quel module contient le code enseignant.

    @return l'idententifiant de l'image construite pour cet exerciseur.
    """
    debug_out = verbose and sys.stderr
    dossier_source = os.path.abspath(dossier_source)
    ex = Exerciseur.avec_type(dossier_source, type_ex, debug_out=debug_out, **kwargs)
    return  ex.construire()
