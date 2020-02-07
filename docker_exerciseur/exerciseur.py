from abc import ABC, abstractmethod, ABCMeta

import docker
import tempfile
import shutil
import os
    
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
    @abstractmethod
    def __init__(self):
        self.rép_travail = None
    
    @abstractmethod
    def copie_source(self) -> None:
        pass

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
            i, _log = self.crée_image()
        return i.id



class ExerciseurDockerfile:
    """
    Une classe pour un exerciseur représenté par un dossier
    contenant un dockerfile.    
    """
    
    def __init__(self, chemin):
        self.chemin_travail = chemin
    
    # Méthodes de Exerciseur
    
    def copie_source(self):
        pass
    
    def prépare_source(self):
        pass

    def finalise_exerciseur_dockerfile(self):
        return self

class ExerciseurDémonPython(Exerciseur):
    """
    Un exerciseur pour un testeur écrit en python (le testeur
    doit implémenter un démon qui écoute des tentatives sur le port 5678).

    @param dossier_code: un dossier contenant le code du démon
    """

    #TODO TODO TODO: mode débug
    
    def __init__(self, dossier_code, nom_démon='daemon.py'):
        self.dossier_code = dossier_code
        self.nom_démon = nom_démon
        self.chemin_travail = None
        self.dockerfile = None
        self.position_démon = '.'

    def utiliser_rép_travail(self, chemin):
        self.rép_travail = chemin

    def copie_source(self):
        dest = self.rép_travail
        shutil.copytree(self.dossier_code, dest)

        
    def prépare_source(self):
        pass

    def écrit_dockerfile(self):
        out = open(self.dossier_code + "/Dockerfile", 'w')
        print("FROM python:alpine3.8", file=out)
        print("COPY", self.position_démon, " /exerciseur", file=out)
        print("WORKDIR /exerciseur", file=out)
        if os.path.isfile(self.dossier_code + "/requirements.txt"):
            print("RUN pip install -r requirements.txt", file=out)
        print("EXPOSE 5678", file=out)
        print("CMD exec python " + self.nom_démon, file=out)
