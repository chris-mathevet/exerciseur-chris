import os

import sys
python_version = sys.version_info
if python_version.minor >= 7:
    from importlib import resources
else:
    import importlib_resources as resources
import shutil

from . import Exerciseur
from .package_python import ExerciseurPackagePython

class ExerciseurTestsPython(ExerciseurPackagePython):
    def __init__(self, dossier_code, nom_module='tests', en_place=False, debug_out=None, **kwargs):
        super().__init__(dossier_code, nom_module=nom_module, nom_classe=None,
                         en_place=en_place, debug_out=debug_out, **kwargs)

    def prépare_source(self):
        if not self.rép_travail:
            raise ValueError("impossible de préparer les sources sans dossier de travail")
        rép_src = self.rép_travail
        rép_outils = os.path.join(rép_src, 'outils_exercices')
        os.mkdir(rép_outils)
        with resources.path('outils_exercices', 'jacadi.py') as chemin_jacadi:
            shutil.copyfile(chemin_jacadi, os.path.join(rép_outils, "jacadi.py"))
        with resources.path('outils_exercices', 'voile.py') as chemin_outils:
            shutil.copyfile(chemin_outils, os.path.join(rép_outils, "voile.py"))
        with resources.path('outils_exercices', '__init__.py') as chemin_init:
            shutil.copyfile(chemin_outils, os.path.join(rép_outils, "__init__.py"))
        with resources.path('outils_exercices', 'code2aes.py') as chemin_code2aes:
            shutil.copyfile(chemin_code2aes, os.path.join(rép_outils, "code2aes.py"))
        super().prépare_source()

    def remplir_main_py(self, out):
        contenu_main = resources.read_text(__package__, 'mainExerciseurTestsPython.py.in')
        contenu_main = contenu_main.replace("{{module}}", self.nom_module)
        out.write(contenu_main)

    def type_exo(self):
        return 'TestsPython'

    def métadonnées(self):
        return {
            'nom_module': self.nom_module
        }

Exerciseur.types_exerciseurs['TestsPython'] = ExerciseurTestsPython
