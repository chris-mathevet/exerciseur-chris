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
import inspect

from outils_exercices import jacadi
from ..tests_python import ExerciseurTestsPython
from .. import Exerciseur
from . import auto_hypothesis

class ExerciseurJacadi(ExerciseurTestsPython):
    def __init__(self, dossier_code, fichier_ens=None, en_place=False, debug_out=None, auto_hypothesis=False, **kwargs):
        self.fichier_ens = fichier_ens
        self.fichiers_aux = None
        self.utiliser_auto_hypothesis = auto_hypothesis
        super().__init__(dossier_code, nom_module=None, en_place=en_place, debug_out=debug_out, **kwargs)

    def prépare_source(self):
        if not self.rép_travail:
            raise ValueError("impossible de préparer les sources sans dossier de travail")
        rép_src = self.rép_travail
        if not self.fichier_ens:
            if os.path.isdir(rép_src) : 
                fichiers = [f for f in os.listdir(rép_src) if f.endswith('.py')]
                if len(fichiers) == 1:
                    self.meta["fichier_ens"] = fichiers[0]
            elif rép_src.endswith('.py'):
                self.meta["fichier_ens"] = os.path.basename(rép_src)
            else:
                raise ValueError("impossible de préparer les sources sans le module de question")
        self.fichier_ens_abs = os.path.abspath(rép_src + "/" + self.fichier_ens)
        if self.fichiers_aux is None:
            self.fichiers_aux = []
            fichiers = [f for f in os.listdir(rép_src) if f.endswith('.py')]
            for f in fichiers:
                if f != self.fichier_ens:
                    f_abs = os.path.abspath(rép_src + "/" + f)
                    self.fichiers_aux.append(f_abs)
        with open(self.fichier_ens_abs, 'r') as original:
            contenu_fichier_ens = original.read()
        with open(self.fichier_ens_abs, 'w') as fichier_ens:
            fichier_ens.write("from outils_exercices.jacadi import solution\n" + contenu_fichier_ens)
        self.nom_module_ens = Path(self.fichier_ens_abs).stem
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
        for nom_fichier_aux in self.fichiers_aux:
            nom_mod_aux = Path(nom_fichier_aux).stem
            mod_aux = ModuleType(nom_mod_aux)
            sys.modules[nom_mod_aux] = mod_aux
            with open(nom_fichier_aux) as fichier_aux:
                exec(fichier_aux.read(), mod_aux.__dict__)
        contenu_module_ens = "import jacadi\n"
        with open(self.fichier_ens_abs) as fichier_ens:
            contenu_module_ens += fichier_ens.read()
        mod_ens = ModuleType('mod_ens')
        sys.modules['mod_ens'] = mod_ens
        sys.modules['jacadi'] = jacadi
        exec(contenu_module_ens, mod_ens.__dict__)
        self.nom_solution, self.solution = jacadi.nom_fonction_ens, jacadi.fonction_ens
        self.arguments = list(inspect.signature(self.solution).parameters)
        self.entrees_visibles = mod_ens.__dict__.get(
            "entrees_visibles", [])
        self.entrees_invisibles = mod_ens.__dict__.get(
            "entrees_invisibles", [])
        if len(self.arguments) == 1:
            self.entrees_visibles = [(e,) for e in self.entrees_visibles]
            self.entrees_invisibles = [(e,) for e in self.entrees_invisibles]
        self.sorties_visibles = self.test_fonction(self.solution, self.entrees_visibles)
        self.sorties_invisibles = self.test_fonction(self.solution, self.entrees_invisibles)
        contenu_test_py = resources.read_text(__name__, 'test_jacadi.py.in')
        contenu_test_py = contenu_test_py.replace("{{solution}}", self.nom_solution)
        contenu_test_py = contenu_test_py.replace("{{es_visibles}}", repr(self.sorties_visibles))
        contenu_test_py = contenu_test_py.replace("{{es_invisibles}}", repr(self.sorties_invisibles))
        nom_générateur = None
        if self.utiliser_auto_hypothesis:
            for e in self.entrees_visibles:
                try:
                    nom_générateur = auto_hypothesis.infère_stratégie(e)
                    break
                except auto_hypothesis.PasAssezSpécifique:
                    pass
                except auto_hypothesis.Ingérable:
                    nom_générateur = None
                    break
        if nom_générateur:
            self.extra_requirements.add("hypothesis")
            imports_hypothesis = ("import hypothesis\n"
                                  "from hypothesis import given\n")
            contenu_test_py = contenu_test_py.replace("{{import_hypothesis}}", imports_hypothesis)
            import_module_ens = "import_module(\"{}\")".format(self.nom_module_ens)
            contenu_test_py = contenu_test_py.replace("{{import_module_ens}}", import_module_ens)
            contenu_test_py = contenu_test_py.replace("{{given}}", "@given({})".format(nom_générateur))
            contenu_test_py = contenu_test_py.replace("{{end_given}}", "")
        else:
            contenu_test_py = contenu_test_py.replace("{{import_hypothesis}}", "")
            contenu_test_py = contenu_test_py.replace("{{import_module_ens}}", "")
            contenu_test_py = contenu_test_py.replace("{{given}}", '"""')
            contenu_test_py = contenu_test_py.replace("{{end_given}}", '"""')
        out.write(contenu_test_py)

    def type_exo(self):
        return 'Jacadi'

    def métadonnées_src(self):
        return {
            'fichier_ens': self.fichier_ens,
            'auto_hypothesis': self.utiliser_auto_hypothesis
        }

    def métadonnées(self):
        def repr_entree(e):
            return tuple(repr(x) for x in e)
        
        repr_entrees_visibles = [repr_entree(e) for e in self.entrees_visibles]
        repr_entrees_invisibles = [repr_entree(e) for e in self.entrees_invisibles]
        repr_sorties_visibles = [(repr_entree(e), repr(s)) for (e,s) in self.sorties_visibles]
        return {
            'fichier_ens': self.fichier_ens,
            "entrees_visibles": repr_entrees_visibles,
            "sorties_visibles": repr_sorties_visibles,
            "entrees_invisibles": repr_entrees_invisibles,
            "arguments": self.arguments,
            "nom_solution": self.nom_solution,
        }

Exerciseur.types_exerciseurs['Jacadi'] = ExerciseurJacadi
