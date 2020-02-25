from abc import ABC, abstractmethod, ABCMeta

from typing import Dict
import docker
import tempfile
import shutil
import os
import sys
import io
import tarfile
from pkg_resources import resource_string
from pathlib import Path
from types import ModuleType

from . import jacadi


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
        rép_source = os.path.join(dest, 'src')
        return Exerciseur.avec_type(rép_source, en_place=True, type_exo = self.type_exo, **self.métadonnées)

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

    def debug(self, *args, **kwargs):
        if self.debug_out:
            print(*args, **kwargs, file=self.debug_out)
        
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
        def renomme(tar_info):
            tar_info.name = tar_info.name.replace(self.sources, 'src')
            return tar_info
        contenu_tar = io.BytesIO()
        t = tarfile.open(fileobj=contenu_tar, mode='w:xz')
        t.add(self.sources, recursive=True, filter=renomme)
        # for (dirname, _, filenames) in os.walk(self.sources):
        #     for filename in filenames:
        #         t.add(os.path.join(dirname, filename))
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
            self.debug("-----------------------")
            self.debug("Logs construction image")
            self.debug("-----------------------")
            for ligne in log:
                self.debug(ligne)
        return i.id



class ExerciseurDockerfile(Exerciseur):
    """
    Une classe pour un exerciseur représenté par un dossier
    contenant un dockerfile.    
    """
    
    def __init__(self, chemin, en_place=True, debug_out=None):
        super().__init__(chemin, en_place=True, debug_out=debug_out)
    
    # Méthodes de Exerciseur

    def métadonnées(self):
        return {}

    def type_exo(self):
        return 'Dockerfile'

    def utiliser_rép_travail(self, rép):
        pass
    
    def copie_source(self):
        pass
    
    def prépare_source(self):
        pass

    def écrit_dockerfile(self):
        pass

Exerciseur.types_exerciseurs['Dockerfile'] = ExerciseurDockerfile

class ExerciseurDémonPython(Exerciseur):
    """
    Un exerciseur pour un testeur écrit en python (le testeur
    doit implémenter un démon qui écoute des tentatives sur le port 5678).

    @param dossier_code: un dossier contenant le code du démon
    """

    def __init__(self, dossier_code, nom_démon='daemon.py', en_place=False, debug_out=None):
        super().__init__(dossier_code, en_place=en_place, debug_out=debug_out)
        self.nom_démon = nom_démon
        self.rép_travail = None
        self.dockerfile = None
        self.position_démon = '.'
        self.debug_out = debug_out

    def utiliser_rép_travail(self, chemin):
        self.rép_travail = chemin

    def copie_source(self):
        dest = self.rép_travail
        self.debug("copie des fichiers source dans ", dest)
        shutil.copytree(self.sources, dest)
        
    def prépare_source(self):
        pass

    def écrit_dockerfile(self):
        out = open(self.rép_travail + "/Dockerfile", 'w')
        self.debug("----------")
        self.debug("Dockerfile")
        self.debug("----------")
        if self.debug_out:
            out = StreamTee(self.debug_out, out)
        print("FROM python:alpine3.8", file=out)
        print("COPY", self.position_démon, " /exerciseur", file=out)
        print("WORKDIR /exerciseur", file=out)
        if os.path.isfile(self.rép_travail + "/requirements.txt"):
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

class ExerciseurPackagePython(ExerciseurDémonPython):
    """
    Un exerciseur pour un testeur donné sous forme d'un package python
    avec une classe SessionÉtudiante.

    La classe SessionÉtudiante a un constructeur (connexion pour commencer
    une tentative) et une méthode évalue(self, codeEtu).
    """
    def __init__(self, dossier_code, nom_classe='ToujoursContent',
                 nom_module='exerciseur', en_place=False, debug_out=None):
        super().__init__(dossier_code, nom_démon=None, en_place=en_place)
        self.nom_classe = nom_classe
        self.nom_module = nom_module

    def prépare_source(self):
        if not self.rép_travail:
            raise ValueError("impossible de préparer le démon sans dossier de travail")
        rép_src = self.rép_travail
        if not os.path.isfile(rép_src + "/setup.py"):
            # pas de setup.py, on va procéder à la main
            nom_main_py = 'demon_exerciseur.py'
            while os.path.isfile(rép_src + "/" + nom_main_py):
                nom_main_py = 'x' + nom_main_py
            with open(rép_src + "/" + nom_main_py, 'w') as f_main_py:
                self.nom_démon = nom_main_py
                self.remplir_main_py(f_main_py)
            with open(rép_src + "/requirements.txt", 'a') as rq:
                self.étendre_requirements(rq)
        else:
            raise ValueError("ExerciseurPackagePython ne sait pas gérer setup.py")

    def étendre_requirements(self, rq):
        rq.write("cbor\n")

    def remplir_main_py(self, out):
        contenu_main = resource_string(__name__, 'mainExerciseurPackagePython.py.in').decode()
        contenu_main = contenu_main.replace("{{NomClasse}}", self.nom_classe)
        contenu_main = contenu_main.replace("{{module}}", self.nom_module)
        out.write(contenu_main)

    def type_exo(self):
        return 'PackagePython'

    def métadonnées(self):
        return {
            'nom_module': self.nom_module,
            'nom_classe': self.nom_classe
        }

Exerciseur.types_exerciseurs['PackagePython'] = ExerciseurPackagePython


class ExerciseurTestsPython(ExerciseurPackagePython):
    def __init__(self, dossier_code, nom_module='tests', en_place=False, debug_out=None):
        super().__init__(dossier_code, nom_module=nom_module, nom_classe=None,
                         en_place=en_place, debug_out=debug_out)

    def prépare_source(self):
        super().prépare_source()

    def remplir_main_py(self, out):
        contenu_main = resource_string(__name__, 'mainExerciseurTestsPython.py.in').decode()
        contenu_main = contenu_main.replace("{{module}}", self.nom_module)
        out.write(contenu_main)

    def type_exo(self):
        return 'TestsPython'

    def métadonnées(self):
        return {
            'nom_module': self.nom_module
        }

Exerciseur.types_exerciseurs['TestsPython'] = ExerciseurTestsPython

class ExerciseurJacadi(ExerciseurTestsPython):
    def __init__(self, dossier_code, fichier_ens=None, en_place=False, debug_out=None):
        self.fichier_ens = fichier_ens
        self.nom_module = fichier_ens
        super().__init__(dossier_code, nom_module=None, en_place=en_place, debug_out=debug_out)

    def prépare_source(self):
        if not self.rép_travail:
            raise ValueError("impossible de préparer les sources sans dossier de travail")
        rép_src = self.rép_travail
        if not self.fichier_ens:
            fichiers = [f for f in os.listdir(rép_src) if f.endswith('.py')]
            if len(fichiers) == 1:
                self.fichier_ens = fichiers[0]
        with open(rép_src + "/jacadi.py", 'wb') as mod_jacadi:
            contenu_mod_jacadi = resource_string(__name__, 'jacadi.py')
            mod_jacadi.write(contenu_mod_jacadi)
        self.fichier_ens_abs = os.path.abspath(rép_src + "/" + self.fichier_ens)
        nom_mod_tests = 'tests'
        while os.path.isfile(rép_src + "/" + nom_mod_tests + ".py"):
            nom_test = x + nom_mod_tests
        self.nom_module = nom_mod_tests
        with open(rép_src + "/" + nom_mod_tests + ".py", 'w') as mod_test:
            self.remplir_test_py(mod_test)
        super().prépare_source()

    def test_fonction(self, fonction, entrees):
        res = []
        for i in entrees:
            res.append((i, fonction(*i)))
        return res
    
    def remplir_test_py(self, out):
        nom_module_ens = Path(self.fichier_ens_abs).stem
        with open(self.fichier_ens_abs) as fichier_ens:
            contenu_module_ens = (fichier_ens.read())
        mod_ens = ModuleType('mod_ens')
        sys.modules['mod_ens'] = mod_ens
        mod_ens.__dict__['solution'] = jacadi.solution
        exec(contenu_module_ens, mod_ens.__dict__)
        solution = [(nom, fun) for nom, fun in mod_ens.__dict__.items(
        ) if "solution" in dir(fun)]
        if solution:
            (self.nom_solution, self.solution) = solution[0]
        self.entrees_visibles = mod_ens.__dict__.get(
            "entrees_visibles", [])
        self.entrees_invisibles = mod_ens.__dict__.get(
            "entrees_invisibles", [])
        self.sorties_visibles = self.test_fonction(self.solution, self.entrees_visibles)
        self.sorties_invisibles = self.test_fonction(self.solution, self.entrees_invisibles)
        contenu_test_py = resource_string(__name__, 'test_jacadi.py.in').decode()
        contenu_test_py = contenu_test_py.replace("{{solution}}", self.nom_solution)
        contenu_test_py = contenu_test_py.replace("{{es_visibles}}", repr(self.sorties_visibles))
        contenu_test_py = contenu_test_py.replace("{{es_invisibles}}", repr(self.sorties_invisibles))
        out.write(contenu_test_py)

    def type_exo(self):
        return 'Jacadi'

    def métadonnées(self):
        return {
            'fichier_ens': self.fichier_ens
        }

Exerciseur.types_exerciseurs['Jacadi'] = ExerciseurJacadi
