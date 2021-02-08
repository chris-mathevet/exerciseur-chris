from abc import ABC, abstractmethod, ABCMeta

from typing import Dict
import docker
import tempfile
import os
import sys
import io
import tarfile
from pathlib import Path
from types import ModuleType
import cbor

from ..stream_tee import StreamTee

class PaquetExercice:
    def __init__(self, contenu: bytes, type_exo, métadonnées):
        self.contenu = contenu
        self.métadonnées = métadonnées
        if 'en_place' in self.métadonnées:
            del self.métadonnées['en_place']
        self.type_exo = type_exo

    def extrait(self, dest: str) -> 'Exerciseur':
        fichier_tar = tarfile.open(fileobj=io.BytesIO(self.contenu), mode='r:xz')
        fichier_tar.extractall(path=dest)
        rép_source = os.path.join(dest, 'src')
        return Exerciseur.avec_type(rép_source, en_place=True, type_exo = self.type_exo, **self.métadonnées)

    def __enter__(self):
        self.rép_extraction = tempfile.TemporaryDirectory()
        nom_rép_extraction = self.rép_extraction.__enter__()
        return self.extrait(nom_rép_extraction)

    def __exit__(self, *args):
        self.rép_extraction.__exit__(*args)

    def to_dict(self) -> Dict:
        return {
            'contenu': self.contenu,
            'métadonnées': self.métadonnées,
            'type_exo': self.type_exo
        }

    def vers_cbor(self) -> bytes:
        return cbor.dumps(self.to_dict())

    @classmethod
    def depuis_cbor(classe, x: bytes):
        return classe.from_dict(cbor.loads(x))


    @classmethod
    def from_dict(Classe, dico):
        return Classe(dico['contenu'], dico['type_exo'], dico['métadonnées'])

class Exerciseur(ABC):
    """
    Cette classe représente un exerciseur. Pour construire une image docker à partir
    d'un objet de cette classe, il faut disposer d'un répertoire de travail.

    On passe ensuite par trois étapes:
    - on copie les sources dans ce répertoire
    - `prépare_source` modifie les sources pour préparer la construction
    - `vers_exerciseur_dockerfile` crée un `ExerciseurDockerfile` pour pouvoir lancer la construction
      de l'image.
    """
    types_exerciseurs = {}

    @abstractmethod
    def __init__(self, sources: str, en_place: False, debug_out=None):
        self.sources = sources
        if en_place:
            self.rép_travail = sources
        else:
            self.rép_travail = None
        self.prêt = en_place
        self.debug_out = debug_out

    def debug(self, *args, **kwargs):
        if self.debug_out:
            print(*args, **kwargs, file=self.debug_out)

    @abstractmethod
    def copie_source(self) -> None:
        pass

    @abstractmethod
    def métadonnées(self) -> Dict[str, str]:
        pass

    def prépare_métadonnées(self):
        self.meta = self.métadonnées()

    @abstractmethod
    def type_exo(self) -> str:
        pass

    def empaquète(self) -> PaquetExercice:
        def renomme(tar_info):
            p = tar_info.name
            if os.path.isabs(self.sources):
                p = os.path.join('/', p)
            p = os.path.relpath(p, start=self.sources)
            p = os.path.join('src', p)
            tar_info.name = p
            return tar_info
        contenu_tar = io.BytesIO()
        t = tarfile.open(fileobj=contenu_tar, mode='w:xz')
        t.add(self.sources, recursive=True, filter=renomme)
        t.close()
        return PaquetExercice(contenu_tar.getvalue(), self.type_exo(), self.métadonnées())

    @classmethod
    def avec_type(cls, répertoire: str, type_exo: str, *args, **kwargs) -> None:
        """
        Construit un exerciseur (de la sous-classe idoine).

        @param type_ex: le type d'exerciseur, parmi "DémonPy", "PackagePy", "TestsPy", "Dockerfile" ou "Jacadi"
        @param répertoire: le dossier contenant les sources de l'exerciseur
        @param kwarg: un dictionnaire qui sert à donner des arguments supplémentaires en fonction de `type_ex`.
        - pour PackagePy, `nom_module="tralala"` indique quel module contient la classe exerciseur et `nom_classe="NomClasse"` le nom de cette classe
        - pour TestsPython, `nom_module="tralala"` indique quel module contient les tests
        - pour Jacadi, `module="mod_ens"` indique quel module contient le code enseignant.

        @return l'objet exerciseur (de la sous-classe idoine d'Exerciseur).
        """
        Classe = cls.types_exerciseurs[type_exo]
        return Classe(répertoire, *args, **kwargs)


    @abstractmethod
    def utiliser_rép_travail(self, rép_travail: str) -> None:
        """
        Indique un répertoire à utiliser comme répertoire de travail pour la construction de l'image docker.
        """
        pass

    @abstractmethod
    def prépare_source(self) -> None:
        """
        Modifie les sources présentes dans rép_travail (si None, utilise le répertoire
        de travail obtenu avec `with self as t`)
        """
        pass

    @abstractmethod
    def écrit_dockerfile(self):
        """
        Finalise la création d'un ExerciseurDockerfile à partir du travail où les sources ont été
        copiées et préparées.
        """
        pass

    def crée_image(self, docker_client=None):
        """Crée l'image docker.

        Renvoie un couple (image, log). L'image est une chaîne de
        caractères contenant le hash de l'image qui a été construite;
        log est un itérateur des lignes du log de construction.
        """
        if not self.rép_travail:
            raise ValueError("rép_travail doit être défini lors de l'appel à crée_image")
        docker_client = docker_client or docker.from_env()
        (image, log) = docker_client.images.build(path=self.rép_travail, quiet=True)
        nom_image=image.id.split(':')[1]
        image.tag('127.0.0.1:5000/exerciseur',nom_image)
        try:
            image.push('127.0.0.1:5000/exerciseur', tag=nom_image)
        except Exception as e:
            print("Exception while pushing:", e)
            pass
        import requests, json
        r = requests.post('http://gateway:8080/system/functions', data=json.dumps({ "service":image.id.split(':')[1][:62], "image":"127.0.0.1:5000/exerciseur:%s"%nom_image }))
        return (image,log)


    def construire(self) -> str:
        """
        Construit une image docker en utilisant comme répertoire de travail
        un répertoire temporaire.

        Renvoie une chaîne de caractères contenant le hash de l'image qui a été construite.
        """
        with tempfile.TemporaryDirectory() as rép_travail:
            self.utiliser_rép_travail(rép_travail + '/src')
            self.copie_source()
            self.prépare_source()
            self.écrit_dockerfile()
            i, log = self.crée_image()
            self.prépare_métadonnées()
            self.debug("-----------------------")
            self.debug("Logs construction image")
            self.debug("-----------------------")
            for ligne in log:
                self.debug(ligne)
        return i.id

    @classmethod
    def register(classe, nom, sous_classe):
        classe.types_exerciseurs[nom] = sous_classe
