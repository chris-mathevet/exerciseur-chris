import os
from pathlib import Path
from types import ModuleType
import sys
python_version = sys.version_info
if python_version.minor >= 7:
    from importlib import resources
else:
    import importlib_resources as resources
import shutil

import jacadi
from ..tests_python import ExerciseurTestsPython
from .. import Exerciseur

class ExerciseurJacadi(ExerciseurTestsPython):
    def __init__(self, dossier_code, fichier_ens=None, en_place=False, debug_out=None):
        self.fichier_ens = fichier_ens
#        self.nom_module = nom_module
        super().__init__(dossier_code, nom_module=None, en_place=en_place, debug_out=debug_out)

    def prépare_source(self):
        if not self.rép_travail:
            raise ValueError("impossible de préparer les sources sans dossier de travail")
        rép_src = self.rép_travail
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
        solution = [(nom, fun) for nom, fun in mod_ens.__dict__.items()
                    if "solution" in dir(fun)]
        assert solution, self.fichier_ens_abs # mod_ens.__dict__
        self.nom_solution, self.solution = solution[0]
        self.entrees_visibles = mod_ens.__dict__.get(
            "entrees_visibles", [])
        self.entrees_invisibles = mod_ens.__dict__.get(
            "entrees_invisibles", [])
        self.sorties_visibles = self.test_fonction(self.solution, self.entrees_visibles)
        self.sorties_invisibles = self.test_fonction(self.solution, self.entrees_invisibles)
        contenu_test_py = resources.read_text(__name__, 'test_jacadi.py.in')
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
