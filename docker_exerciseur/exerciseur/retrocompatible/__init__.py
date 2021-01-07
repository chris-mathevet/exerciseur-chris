# import os
# from pathlib import Path
# from types import ModuleType
import sys
python_version = sys.version_info
if python_version.minor >= 7:
    from importlib import resources
else:
    import importlib_resources as resources
import shutil

# from outils_exercices import jacadi
from ..dockerfile import ExerciseurDockerfile
from .. import Exerciseur


class ExerciseurRetrocompatible(Exerciseur):

    def __init__(self, chemin, en_place=False, debug_out=None):
        super().__init__(chemin, en_place=en_place, debug_out=debug_out)
        self.typeExo=None

    def utiliser_rép_travail(self, chemin):
        self.rép_travail = chemin

    def copie_source(self):
        dest = self.rép_travail
        self.debug("copie des fichiers source dans ", dest)
        shutil.copytree(self.sources, dest)

    def écrit_dockerfile(self):
        with open(self.rép_travail + "/run.py", 'w') as out:
            #if self.debug_out:
            #    out = StreamTee(self.debug_out, out)
            contenu_run_py = resources.read_text(__name__, 'run.py.in')
            contenu_run_py = contenu_run_py.replace("{{typeExo}}", self.typeExo)
            out.write(contenu_run_py)
        with open(self.rép_travail + "/Dockerfile", 'w') as out:
            #if self.debug_out:
            #    out = StreamTee(self.debug_out, out)
            contenu_Dockerfile = resources.read_text(__name__, 'Dockerfile.in')
            out.write(contenu_Dockerfile)

    def métadonnées(self):
        return {}

    def type_exo(self):
        return self.typeExo


    def prépare_source(self):
        pass

    # def type_exo(self):
    #     return 'Jacadi'

def getRetroClasse(typeExo):
    class ExerciseurRetrocompatibleType(ExerciseurRetrocompatible):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.typeExo=typeExo
    return ExerciseurRetrocompatibleType

for typeExo in {"java","python"}:
    Exerciseur.types_exerciseurs[typeExo] = getRetroClasse(typeExo)
