import docker
import io
import tempfile
import os
import sys
import shutil
import argparse
import importlib
from pkg_resources import resource_string
from pathlib import Path
from types import ModuleType
from . import jacadi

parser = argparse.ArgumentParser(add_help=False)

parser.add_argument(
    "dossier", help="Le dossier contenant les sources de l'exerciseur",
    nargs='?'
)
parser.add_argument(
    "--type", help="Le type d'exerciseur à construire (par défaut, %(default)s)",
    choices=["DémonPy", "PackagePy", "TestsPy", "Dockerfile", "Jacadi"],
    default="DémonPy"
)
parser.add_argument(
    "--classe", help="la classe exerciseur, pour les exerciseurs type PackagePython"
)
parser.add_argument(
    "--module", help="le module de tests de l'exerciseur"
)

class ExerciseurDockerfile:
    """
    Une classe pour un exerciseur représenté par un dossier
    contenant un dockerfile.    
    """
    
    def __init__(self, chemin):
        self.chemin = chemin

    def __enter__(self):
        pass

    def __exit__(self, *args):
        pass

    def construit(self):
        return self.crée_image()
    
    def crée_image(self, docker_client=None):
        """
        Crée l'image docker
        """
        docker_client = docker_client or docker.from_env()
        return docker_client.images.build(path=self.chemin)
    
class StreamTee:
    def __init__(self, out1, out2):
        self.out1 = out1
        self.out2 = out2

    def write(self, *args, **kwargs):
        self.out1.write(*args, **kwargs)
        self.out2.write(*args, **kwargs)

class ExerciseurDémonPython:
    """
    Un exerciseur pour un testeur écrit en python (le testeur
    doit implémenter un démon qui écoute des tentatives sur le port 5678).

    @param dossier_code: un dossier contenant le code du démon
    """
    def __init__(self, dossier_code, nom_démon='daemon.py'):
        self.dossier_code = dossier_code
        self.nom_démon = nom_démon
        self.chemin_travail = None
        self.dockerfile = None

    def copie_source(self):
        self.chemin_travail = self.rép_travail.__enter__()
        dest = self.chemin_travail + '/src'
        shutil.copytree(self.dossier_code, dest)

    def prépare_source(self):
        pass

    def __enter__(self):
        self.rép_travail = tempfile.TemporaryDirectory()        

    def __exit__(self, *args):
        self.rép_travail.__exit__(*args)
        
    def crée_image(self, docker_client=None):
        if self.chemin_travail:
            if self.dockerfile:
                    self.remplir_dockerfile(df, position='src', from_scratch=False)
            if not self.dockerfile:
                self.dockerfile = self.chemin_travail + "/Dockerfile"
                with open(self.dockerfile, 'w') as df:
                    self.remplir_dockerfile(df, position='src', from_scratch=True)
            ex_df = ExerciseurDockerfile(self.chemin_travail)
            return ex_df.crée_image(docker_client)
        else:
            raise ValueError("impossible de créer une image pour un %r sans dossier de travail" % type(self))

    def construit(self):
        self.copie_source()
        self.prépare_source()
        return self.crée_image()


    def remplir_dockerfile(self, out, position='.', from_scratch=False):
        """
        @param position: l'endroit où le code du démon sera accessible pour le
                         Dockerfile (par défaut, '.')
        @param out: un descripteur de fichier pour le Dockerfile à créer
        @param debug_out: une sortie de débogage
        """
        if from_scratch:
            print("FROM python:alpine3.8", file=out)
        print("COPY", position, " /exerciseur", file=out)
        print("WORKDIR /exerciseur", file=out)
        if os.path.isfile(self.dossier_code + "/requirements.txt"):
            print("RUN pip install -r requirements.txt", file=out)
        print("EXPOSE 5678", file=out)
        print("CMD exec python " + self.nom_démon, file=out)
            
class ExerciseurPackagePython(ExerciseurDémonPython):
    """
    Un exerciseur pour un testeur donné sous forme d'un package python
    avec une classe SessionÉtudiante.

    La classe SessionÉtudiante a un constructeur (connexion pour commencer
    une tentative) et une méthode évalue(self, codeEtu).
    """
    def __init__(self, dossier_code, classe_session_étudiante='ToujoursContent', nom_module='exerciseur'):
        super().__init__(dossier_code, nom_démon=None)
        self.nom_classe = classe_session_étudiante
        self.nom_module = nom_module

    def prépare_source(self):
        if not self.chemin_travail:
            raise ValueError("impossible de préparer le démon sans dossier de travail")
        rép_src = self.chemin_travail + "/src"
        self.dossier_code = rép_src
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

class ExerciseurTestsPython(ExerciseurPackagePython):
    def __init__(self, dossier_code, nom_module='tests'):
        super().__init__(dossier_code, nom_module=nom_module, classe_session_étudiante=None)

    def prépare_source(self):
        super().prépare_source()
        rép_src = self.chemin_travail + "/src"
        with open(rép_src + "/jacadi.py", 'wb') as mod_jacadi:
            contenu_mod_jacadi = resource_string(__name__, 'jacadi.py')
            mod_jacadi.write(contenu_mod_jacadi)

    def remplir_main_py(self, out):
        contenu_main = resource_string(__name__, 'mainExerciseurTestsPython.py.in').decode()
        contenu_main = contenu_main.replace("{{module}}", self.nom_module)
        out.write(contenu_main)

class ExerciseurJacadi(ExerciseurTestsPython):
    def __init__(self, dossier_code, fichier_ens=None):
        self.fichier_ens = fichier_ens
        self.nom_module = fichier_ens
        super().__init__(dossier_code, nom_module=None)

    def prépare_source(self):
        if not self.chemin_travail:
            raise ValueError("impossible de préparer les sources sans dossier de travail")
        rép_src = self.chemin_travail + "/src"
        if not self.fichier_ens:
            fichiers = [f for f in os.listdir(rép_src) if f.endswith('.py')]
            if len(fichiers) == 1:
                self.fichier_ens = fichiers[0]
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
        

        
def main(args):
    dossier_source = args.dossier or "."
    construit_exerciseur(args.type, dossier_source, args.verbose, classe=args.classe, module=args.module )


def construit_exerciseur(type_ex, dossier_source, verbose, **kwargs):
    """
    Construit un exerciseur. Les arguments correspondent à ceux de `docker-exerciseur construit`

    @param type_ex: le type d'exerciseur, parmi "DémonPy", "PackagePy", "TestsPy", "Dockerfile" ou "Jacadi"
    @param dossier_source: le dossier contenant les sources de l'exerciseur
    @param verbose: un booléen, vrai pour afficher plus d'informations sur sys.stderr
    @param kwarg: un dictionnaire qui sert à donner des arguments supplémentaires en fonction de `type_ex`.
    - pour PackagePy, `module="nom_module"` indique quel module contient la classe exerciseur et `classe="NomClasse"` le nom de cette classe
    - pour TestsPy, `module="nom_module"` indique quel module contient les tests
    - pour Jacadi, `module="mod_ens"` indique quel module contient le code enseignant.

    @return l'idententifiant de l'image construite pour cet exerciseur.
    """
    debug_out = verbose and sys.stderr
    dossier_source = os.path.abspath(dossier_source)
    if type_ex == "Dockerfile":
        ex = ExerciseurDockerfile(dossier_source)
    elif type_ex == "PackagePy":
        ex = ExerciseurPackagePython(dossier_source, kwargs["classe"], kwargs["module"])
    elif type_ex == "TestsPy":
        ex = ExerciseurTestsPython(dossier_source, nom_module=kwargs["module"])
    elif type_ex == "Jacadi":
        ex = ExerciseurJacadi(dossier_source, fichier_ens=kwargs["module"])
    else:
        ex = ExerciseurDémonPython(dossier_source)

    with ex:
        if verbose:
            ex.copie_source()
            ex.prépare_source()
            with open(ex.chemin_travail + "/Dockerfile", 'w') as dockerfile:
                print("----------", file=sys.stderr)
                print("Dockerfile", file=sys.stderr)
                print("----------", file=sys.stderr)
                dockerfile = StreamTee(sys.stderr, dockerfile)
                ex.remplir_dockerfile(dockerfile, position = "src", from_scratch=True)
            (img, log) = ex.crée_image()
            print("-----------------", file=sys.stderr)
            print("Log constr. image", file=sys.stderr)
            print("-----------------", file=sys.stderr)
            for line in log:
                print(line, file=sys.stderr)

        else:
            (img, _log) = ex.construit()
    return img.id
