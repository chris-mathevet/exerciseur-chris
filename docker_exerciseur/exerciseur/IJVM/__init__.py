import sys
import os
python_version = sys.version_info
from pathlib import Path
from types import ModuleType
if python_version.minor >= 7:
    from importlib import resources
else:
    import importlib_resources as resources
import shutil

from outils_exercices import jacadi
from ..dockerfile import ExerciseurDockerfile
from .. import Exerciseur
import inspect

class ExerciseurIJVM(Exerciseur):

    def __init__(self, chemin, en_place=False, debug_out=None, **kwargs):
        super().__init__(chemin, en_place=en_place, debug_out=debug_out, **kwargs)
        self.avec_openfaas = kwargs.get("avec_openfaas", True)
        self.meta = kwargs
        self.typeExo = "ijvm"

    def utiliser_rép_travail(self, chemin):
        self.rép_travail = chemin

    def copie_source(self):
        dest = self.rép_travail
        self.debug("copie des fichiers source dans ", dest)
        shutil.copytree(self.sources, dest)

    def prépare_source(self):
        with resources.path(__name__,"exerciseur.jar") as exerciseur_jar:
            shutil.copyfile(exerciseur_jar, self.rép_travail +"/exerciseur.jar")
        with open(self.rép_travail + "/run.py", 'w') as out:
                contenu_run_py = resources.read_text(__name__, 'testSolution.py.in')
                contenu_run_py = contenu_run_py.replace("{{code_solution}}", str(self.meta.get("codeSolution", "")))
                out.write(contenu_run_py)

    def écrit_dockerfile(self):
        with open(self.rép_travail + "/Dockerfile", 'w') as out:
            contenu_Dockerfile = resources.read_text(__name__, 'Dockerfile.in')
            out.write(contenu_Dockerfile)

    def métadonnées(self):
        return self.meta

    def type_exo(self):
        return self.typeExo


Exerciseur.types_exerciseurs["ijvm"] = ExerciseurIJVM
