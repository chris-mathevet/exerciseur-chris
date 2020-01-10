import docker
import io
import tempfile
import os
import sys
import shutil
import argparse
from pkg_resources import resource_string


parser = argparse.ArgumentParser()
parser.add_argument(
    "--verbose", help="affiche plus d'informations", action="store_true"
)
parser.add_argument(
    "--dossier-python", help="un dossier avec un daemon.py"
)
parser.add_argument(
    "--classe", help="une classe exerciseur"
)

class ExerciseurDockerfile:
    """
    Une classe pour un exerciseur représenté par un dossier
    contenant un dockerfile.    
    """
    
    def __init__(self, chemin):
        self.chemin = chemin
    
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

    def prépare_copie_travail(self):
        self.rép_travail = tempfile.TemporaryDirectory()
        
        self.chemin_travail = self.rép_travail.__enter__()
        dest = self.chemin_travail + '/src'
        shutil.copytree(dossier_python, dest)

    def __enter__(self):
        self.prépare_copie_travail()

    def __exit__(self, *args):
        self.rép_travail.__exit__(*args)
        
    def crée_image(self, docker_client=None):
        if self.chemin_travail:
            if not self.dockerfile:
                self.dockerfile = self.chemin_travail + "/Dockerfile"
                with open(self.dockerfile, 'w') as df:
                    self.remplir_dockerfile(df, position='src')
            ex_df = ExerciseurDockerfile(self.chemin_travail)
            return ex_df.crée_image(docker_client)
        else:
            raise ValueError("impossible de créer une image pour un %r sans dossier de travail" % type(self))

    def remplir_dockerfile(self, out, position='.'):
        """
        @param position: l'endroit où le code du démon sera accessible pour le
                         Dockerfile (par défaut, '.')
        @param out: un descripteur de fichier pour le Dockerfile à créer
        @param debug_out: une sortie de débogage
        """
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
    def __init__(self, dossier_code, classe_session_étudiante='ToujoursContent'):
        super().__init__(dossier_code, nom_démon=None)
        self.nom_classe = classe_session_étudiante
        self.nom_module = 'exerciseur'

    def prépare_démon(self):
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
                rq.write("cbor\n")
        else:
            raise ValueError("ExerciseurPackagePython ne sait pas gérer setup.py")

    def remplir_main_py(self, out):
        contenu_main = resource_string(__name__, 'mainExerciseurPackagePython.py').decode()
        contenu_main = contenu_main.replace("{{NomClasse}}", self.nom_classe)
        contenu_main = contenu_main.replace("{{module}}", self.nom_module)
        out.write(contenu_main)
        
    def __enter__(self):
        super().__enter__()
        self.prépare_démon()
    
if __name__ == "__main__":
    args = parser.parse_args()
    debug_out = args.verbose and sys.stderr
    dossier_python = args.dossier_python or "."
    dossier_python = os.path.abspath(dossier_python)
    if args.classe:
        ex = ExerciseurPackagePython(dossier_python, args.classe)
    else:
        ex = ExerciseurDémonPython(dossier_python)

    if args.verbose:
        with tempfile.TemporaryDirectory() as dossier_construction:
            dest = dossier_construction + "/src"
            shutil.copytree(dossier_python, dest)
            ex.chemin_travail = dossier_construction
            if args.classe:
                ex.prépare_démon()
            with open(dossier_construction + "/Dockerfile", 'w') as dockerfile:
                print("----------", file=sys.stderr)
                print("Dockerfile", file=sys.stderr)
                print("----------", file=sys.stderr)
                dockerfile = StreamTee(sys.stderr, dockerfile)
                ex.remplir_dockerfile(dockerfile, position = "src")
            (img, log) = ex.crée_image()
            print("-----------------", file=sys.stderr)
            print("Log constr. image", file=sys.stderr)
            print("-----------------", file=sys.stderr)
            for line in log:
                print(line, file=sys.stderr)
    else:
        with ex:
            (img, _log) = ex.crée_image()
    print(img.id)
