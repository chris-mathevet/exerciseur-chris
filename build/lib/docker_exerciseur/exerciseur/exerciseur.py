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

def sectionize(message):
    n = len(message)
    souligne = "\n" + n * "-" + "\n"
    return (souligne + message + souligne)

class PaquetExercice:
    def __init__(self, contenu: bytes, type_exo, métadonnées):
        self.contenu = contenu
        self.métadonnées = métadonnées
        if 'en_place' in self.métadonnées:
            del self.métadonnées['en_place']
        self.type_exo = type_exo

    def extrait(self, dest: str) -> 'Exerciseur':
        print(sectionize("EXTRACTION"))
        fichier_tar = tarfile.open(fileobj=io.BytesIO(self.contenu), mode='r:xz')
        print("Membres : ", fichier_tar.getmembers())
        print("\nContenu de l'archive :")
        for member in fichier_tar.getmembers():
            print(f"Nom : {member.name}")
            print(f"Type : {'Répertoire' if member.isdir() else 'Fichier'}")
            print(f"Taille : {member.size} octets")
            print(f"Permissions : {oct(member.mode)}")
            print(f"Date de modification : {member.mtime}")
            print('-' * 50)
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
    def __init__(self, sources: str, en_place: False, debug_out=None, **kwargs):
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


    def métadonnées_src(self) -> Dict[str, str]:
        return self.métadonnées()

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
            
            # Vérification, est ce que self.sources est un répertoire
            if os.path.isdir(self.sources):
                if os.path.isabs(self.sources):
                    p = os.path.join('/', p)
                p = os.path.relpath(p, start=self.sources)
            else:
                # Si ce n'est pas un dossier, on garde juste le nom du fichier, pour éviter d'obtenir src/.
                p = os.path.basename(p)
            p = os.path.join('src', p)
            tar_info.name = p
            return tar_info
        contenu_tar = io.BytesIO()
        t = tarfile.open(fileobj=contenu_tar, mode='w:xz')
        t.add(self.sources, recursive=True, filter=renomme)
        t.close()
        return PaquetExercice(contenu_tar.getvalue(), self.type_exo(), self.métadonnées_src())

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
            docker_client.images.push('127.0.0.1:5000/exerciseur', tag=nom_image)
        except Exception as e:
            print("Exception while pushing:", e)
            pass
        import requests, json
        if self.avec_openfaas:
            nom_fonction = image.id.split(":")[1][:62]
            requests.post('http://gateway:8080/system/functions', data=json.dumps({ "service":nom_fonction, "image":"127.0.0.1:5000/exerciseur:%s"%nom_image }),  headers={"Content-Type": "application/json"})
            requests.post('http://gateway:8080/system/scale-function/'+nom_fonction, data=json.dumps({ "service":nom_fonction, "replicas":0 }),  headers={"Content-Type": "application/json"})
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
        # paquet = self.empaquète().vers_cbor()
        # files = {'moduleEns': self.empaquète().vers_cbor()}

        print(sectionize("DATA PERSO"))
        print(self.empaquète().vers_cbor())
        print(sectionize("DATA SEND"))
        print( b'\xa3gcontenuY\x01d\xfd7zXZ\x00\x00\x04\xe6\xd6\xb4F\x02\x00!\x01\x16\x00\x00\x00t/\xe5\xa3\xe0\'\xff\x01"]\x009\x9c\x88\x86\x12n\xa5\x86\xe4<\xa2\x9b<\x1e\x93\xaa\xa1\xdc\xd2\x17 {\xce]\t}\xfc:\x91G*\xcf\x9a\x84\x19\xd3\xe4\'h\xaa\x15\x15\x8e\x81\xf8\xbd\xdfF\x14\xaf\xfb\xb2\x1a\xfd\x00c[\x90\x06\xab\xa7 \xd9\x84\xacj\xbf\x80\xd8\xc3\xdc\xd7\x85\xadQ2\xf6\x87u\xdd\x923;8\x9b\x0cCMpt\xf7\xd6\xb5\x86O\x12y+C\x89LP\xcf\\\x90[\xfa@\xc0\xbe\xa7u\xfbH\xdb\x95\xbb\x07hL\xe8\xf6\xaf\xb3S1\xf7\x83w\x82\xc8\xd4\xe6%lD\x0bE\xca\x00{\xbd`b\xec\xd2\xe6\x9d8\x90\x8b\x9b>\xaa\x89y\x05\xfb5\x8e\x8e\xf3MqI\x83\x81v1{w\xa7l\x9c5\x92o\xf3#Ox\x89\x13\x80W\xc5\xfc32\xbd03q\x15e\x91\xaaY\xfb\x9d\xb7\\\x8e\xc5>\xfe\x87\x1f\x9ad\xd5\x05\x16\xe3a\xafd\xe5K E\xb4d\x19\x04\x8c\x84,\xf9sp\x86\xb5\'\x9d\xd8\x92\x15\x82\x9c`.\xb1\xced\x0b\xd3\x8e\x1e\x88]s\xcc^4\xe3\xedw\x86d\xe0\x85\xd0\xa4\x7f\xc9\x871\xf9W\xf9zL\xed~\xd5\xeb\xa5\x82:=}\x83\xa3\x14\xa7L\x0ev`\x00\x00\x00E\x1a\xbeXM\xbd\xf3\xa9\x00\x01\xbe\x02\x80P\x00\x003m\xb0\x18\xb1\xc4g\xfb\x02\x00\x00\x00\x00\x04YZmm\xc3\xa9tadonn\xc3\xa9es\xa2kfichier_ens\xf6oauto_hypothesis\xf4htype_exofJacadi')

        exo = PaquetExercice.depuis_cbor(bytes( b'\xa3gcontenuY\x01d\xfd7zXZ\x00\x00\x04\xe6\xd6\xb4F\x02\x00!\x01\x16\x00\x00\x00t/\xe5\xa3\xe0\'\xff\x01"]\x009\x9c\x88\x86\x12n\xa5\x86\xe4<\xa2\x9b<\x1e\x93\xaa\xa1\xdc\xd2\x17 {\xce]\t}\xfc:\x91G*\xcf\x9a\x84\x19\xd3\xe4\'h\xaa\x15\x15\x8e\x81\xf8\xbd\xdfF\x14\xaf\xfb\xb2\x1a\xfd\x00c[\x90\x06\xab\xa7 \xd9\x84\xacj\xbf\x80\xd8\xc3\xdc\xd7\x85\xadQ2\xf6\x87u\xdd\x923;8\x9b\x0cCMpt\xf7\xd6\xb5\x86O\x12y+C\x89LP\xcf\\\x90[\xfa@\xc0\xbe\xa7u\xfbH\xdb\x95\xbb\x07hL\xe8\xf6\xaf\xb3S1\xf7\x83w\x82\xc8\xd4\xe6%lD\x0bE\xca\x00{\xbd`b\xec\xd2\xe6\x9d8\x90\x8b\x9b>\xaa\x89y\x05\xfb5\x8e\x8e\xf3MqI\x83\x81v1{w\xa7l\x9c5\x92o\xf3#Ox\x89\x13\x80W\xc5\xfc32\xbd03q\x15e\x91\xaaY\xfb\x9d\xb7\\\x8e\xc5>\xfe\x87\x1f\x9ad\xd5\x05\x16\xe3a\xafd\xe5K E\xb4d\x19\x04\x8c\x84,\xf9sp\x86\xb5\'\x9d\xd8\x92\x15\x82\x9c`.\xb1\xced\x0b\xd3\x8e\x1e\x88]s\xcc^4\xe3\xedw\x86d\xe0\x85\xd0\xa4\x7f\xc9\x871\xf9W\xf9zL\xed~\xd5\xeb\xa5\x82:=}\x83\xa3\x14\xa7L\x0ev`\x00\x00\x00E\x1a\xbeXM\xbd\xf3\xa9\x00\x01\xbe\x02\x80P\x00\x003m\xb0\x18\xb1\xc4g\xfb\x02\x00\x00\x00\x00\x04YZmm\xc3\xa9tadonn\xc3\xa9es\xa2kfichier_ens\xf6oauto_hypothesis\xf4htype_exofJacadi'))
        # print(sectionize("DATA"))
        # data = {"auteur" : "nobody", "titre":"default", "metaInfos": "{}", 'type': "Jacadi"}
        # print(data)
        # print(sectionize("FILES"))
        # print(files)
        # print(sectionize("FIN FILES"))
        with exo as ex:   
            print(ex.type_exo())
        return i.id

    @classmethod
    def register(classe, nom, sous_classe):
        classe.types_exerciseurs[nom] = sous_classe

def liberer_openfaas(id_exo: str):
    import requests, json
    # r = requests.delete('http://gateway:8080/system/functions', data=json.dumps({ "functionName":id_exo}))
    r = requests.delete(f'http://gateway:8080/function/{id_exo}')
