import os
import sys
python_version = sys.version_info
if python_version.minor >= 7:
    from importlib import resources
else:
    import importlib_resources as resources


from . import Exerciseur
from .demon_python import ExerciseurDémonPython

class ExerciseurPackagePython(ExerciseurDémonPython):
    """
    Un exerciseur pour un testeur donné sous forme d'un package python
    avec une classe SessionÉtudiante.

    La classe SessionÉtudiante a un constructeur (connexion pour commencer
    une tentative) et une méthode évalue(self, codeEtu).
    """
    def __init__(self, dossier_code, nom_classe='ToujoursContent',
                 nom_module='exerciseur', en_place=False, debug_out=None, **kwargs):
        super().__init__(dossier_code, nom_démon=None, en_place=en_place, debug_out=debug_out, **kwargs)
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
        contenu_main = resources.read_text(__package__, 'mainExerciseurPackagePython.py.in')
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
