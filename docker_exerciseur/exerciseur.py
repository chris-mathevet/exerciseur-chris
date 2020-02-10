from abc import ABC, abstractmethod, ABCMeta

from typing import Dict
import docker
import tempfile
import shutil
import os
import sys
import io
import tarfile

class StreamTee:
    def __init__(self, out1, out2):
        self.out1 = out1
        self.out2 = out2

    def write(self, *args, **kwargs):
        self.out1.write(*args, **kwargs)
        self.out2.write(*args, **kwargs)


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
        return Exerciseur.avec_type(dest, en_place=True, type_exo = self.type_exo, **self.métadonnées)

    def __enter__(self):
        self.rép_extraction = tempfile.TemporaryDirectory()
        nom_rép_extraction = self.rép_extraction.__enter__()
        return self.extrait(nom_rép_extraction)

    def __exit__(self, *args):
        self.rép_extraction.__exit__(*args)
        


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
        
    @abstractmethod
    def copie_source(self) -> None:
        pass

    @abstractmethod
    def métadonnées(self) -> Dict[str, str]:
        pass

    @abstractmethod
    def type_exo(self) -> str:
        pass

    def empaquète(self) -> PaquetExercice:
        contenu_tar = io.BytesIO()
        t = tarfile.open(fileobj=contenu_tar, mode='w:xz')
        for (dirname, _, filenames) in os.walk(self.sources):
            for filename in filenames:
                t.add(os.path.join(dirname, filename))
        t.close()
        return PaquetExercice(contenu_tar.getvalue(), self.type_exo(), self.métadonnées())
    
    @classmethod
    def avec_type(cls, répertoire: str, type_exo: str, *args, **kwargs) -> None:
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
        return docker_client.images.build(path=self.rép_travail, quiet=True)

    
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
            if self.debug_out:
                print("-----------------------", file=self.debug_out)
                print("Logs construction image", file=self.debug_out)
                print("-----------------------", file=self.debug_out)
                for ligne in log:
                    print(ligne)
        return i.id



class ExerciseurDockerfile:
    """
    Une classe pour un exerciseur représenté par un dossier
    contenant un dockerfile.    
    """
    
    def __init__(self, chemin, debug_out=None):
        self.chemin_travail = chemin
    
    # Méthodes de Exerciseur
    
    def copie_source(self):
        pass
    
    def prépare_source(self):
        pass

    def écrit_dockerfile(self):
        pass

class ExerciseurDémonPython(Exerciseur):
    """
    Un exerciseur pour un testeur écrit en python (le testeur
    doit implémenter un démon qui écoute des tentatives sur le port 5678).

    @param dossier_code: un dossier contenant le code du démon
    """

    def __init__(self, dossier_code, nom_démon='daemon.py', en_place=False, debug_out=None):
        super().__init__(dossier_code, en_place=en_place, debug_out=debug_out)
        self.dossier_code = dossier_code
        self.nom_démon = nom_démon
        self.rép_travail = None
        self.dockerfile = None
        self.position_démon = '.'
        self.debug_out = debug_out

    def utiliser_rép_travail(self, chemin):
        self.rép_travail = chemin

    def copie_source(self):
        dest = self.rép_travail
        if self.debug_out:
            print("copie des fichiers source dans ", dest)
        shutil.copytree(self.dossier_code, dest)

        
    def prépare_source(self):
        pass

    def écrit_dockerfile(self):
        out = open(self.rép_travail + "/Dockerfile", 'w')
        print("----------", file=self.debug_out)
        print("Dockerfile", file=self.debug_out)
        print("----------", file=self.debug_out)
        if self.debug_out:
            out = StreamTee(sys.stderr, out)
        print("FROM python:alpine3.8", file=out)
        print("COPY", self.position_démon, " /exerciseur", file=out)
        print("WORKDIR /exerciseur", file=out)
        if os.path.isfile(self.dossier_code + "/requirements.txt"):
            print("RUN pip install -r requirements.txt", file=out)
        print("EXPOSE 5678", file=out)
        print("CMD exec python " + self.nom_démon, file=out)

    def métadonnées(self):
        return {
            'nom_démon': self.nom_démon,
            }
        
    def type_exo(self):
        return 'DémonPython'

Exerciseur.types_exerciseurs['DémonPython'] = ExerciseurDémonPython
