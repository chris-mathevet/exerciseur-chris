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

class ExerciseurRetrocompatibleJava(Exerciseur):

    def __init__(self, chemin, en_place=False, debug_out=None, **kwargs):
        super().__init__(chemin, en_place=en_place, debug_out=debug_out, **kwargs)
        self.avec_openfaas = kwargs.get("avec_openfaas", True)
        self.meta = kwargs
        self.typeExo = "java"

    def utiliser_rép_travail(self, chemin):
        self.rép_travail = chemin

    def copie_source(self):
        dest = self.rép_travail
        self.debug("copie des fichiers source dans ", dest)
        shutil.copytree(self.sources, dest)

    def écrit_dockerfile(self):
        from shutil import copyfile
        copyfile(self.rép_travail +"/"+ self.meta.get("nom_classe_test")+".java", self.rép_travail +"/code_ens")
        with open(self.rép_travail + "/run.py", 'w') as out:
                #if self.debug_out:
                #    out = StreamTee(self.debug_out, out)
                contenu_run_py = resources.read_text(__name__, 'run_java.py.in')
                contenu_run_py = contenu_run_py.replace("{{typeExo}}", self.typeExo)
                # contenu_run_py = contenu_run_py.replace("{{classeTest}}", contenu_classe_test)
                for elem in self.meta:
                    contenu_run_py = contenu_run_py.replace("{{%s}}"%elem, str(self.meta.get(elem)))

                out.write(contenu_run_py)
        with open(self.rép_travail + "/Dockerfile", 'w') as out:
            #if self.debug_out:
            #    out = StreamTee(self.debug_out, out)
            contenu_Dockerfile = resources.read_text(__name__, 'Dockerfile.java.in')
            out.write(contenu_Dockerfile)

    def métadonnées(self):
        return self.meta

    def type_exo(self):
        return self.typeExo

    def prépare_source(self):
        pass


class ExerciseurRetrocompatiblePython(Exerciseur):

    def __init__(self, chemin, en_place=False, debug_out=None, **kwargs):
        super().__init__(chemin, en_place=en_place, debug_out=debug_out, **kwargs)
        self.typeExo="python"
        self.meta = kwargs
        self.avec_openfaas = kwargs.get("avec_openfaas", True)
        if self.meta.get("fichier_ens") is None:
            if os.path.isdir(chemin) : 
                fichiers = [f for f in os.listdir(chemin) if f.endswith('.py')]
                if len(fichiers) == 1:
                    self.meta["fichier_ens"] = fichiers[0]
            elif chemin.endswith('.py'):
                self.meta["fichier_ens"] = os.path.basename(chemin)
            else:
                raise ValueError("impossible de préparer les sources sans le module de question")

    def utiliser_rép_travail(self, chemin):
        self.rép_travail = chemin

    def copie_source(self):
        dest = self.rép_travail
        self.debug("copie des fichiers source dans ", dest)
        shutil.copytree(self.sources, dest)

    def écrit_dockerfile(self):
        from shutil import copyfile
        if os.path.isdir(self.sources): # Si source est un dossier
            copyfile(self.sources +"/"+ self.meta.get("fichier_ens"), self.rép_travail +"/code_ens")
        else : # Si source est un fichier, il correspond au fichier de réponses
            copyfile(self.sources, self.rép_travail +"/code_ens")

        with open(self.rép_travail + "/run.py", 'w') as out:
                #if self.debug_out:
                #    out = StreamTee(self.debug_out, out)
                contenu_run_py = resources.read_text(__name__, 'run_python.py.in')
                contenu_run_py = contenu_run_py.replace("{{typeExo}}", self.typeExo)
                for elem in self.meta:
                    contenu_run_py = contenu_run_py.replace("{{%s}}"%elem, str(self.meta.get(elem)))

                out.write(contenu_run_py)
        with open(self.rép_travail + "/Dockerfile", 'w') as out:
            #if self.debug_out:
            #    out = StreamTee(self.debug_out, out)
            contenu_Dockerfile = resources.read_text(__name__, 'Dockerfile.python.in')
            out.write(contenu_Dockerfile)

    def test_fonction(self, fonction, entrees):
        res = []
        for i in entrees:
            res.append((i, fonction(*i)))
        return res

    def métadonnées(self):
        return self.meta

    def prépare_métadonnées(self):
        self.fichier_ens_abs = os.path.abspath(self.rép_travail + "/code_ens")
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
        self.meta["nom_solution"], self.solution = solution[0]
        self.meta["entrees_visibles"] = mod_ens.__dict__.get(
            "entrees_visibles", [])
        self.meta["entrees_invisibles"] = mod_ens.__dict__.get(
            "entrees_invisibles", [])
        self.arguments = list(inspect.signature(self.solution).parameters)
        if len(self.arguments) == 1:
            self.meta["entrees_visibles"] = [(e,) for e in self.meta["entrees_visibles"]]
            self.meta["entrees_invisibles"] = [(e,) for e in self.meta["entrees_invisibles"]]
        self.meta["sorties_visibles"] = self.test_fonction(self.solution, self.meta["entrees_visibles"])
        self.meta["sorties_invisibles"] = self.test_fonction(self.solution, self.meta["entrees_invisibles"])
        self.meta["arguments"] = inspect.getfullargspec(self.solution).args

    def type_exo(self):
        return self.typeExo

    def prépare_source(self):
        pass



Exerciseur.types_exerciseurs["java"] = ExerciseurRetrocompatibleJava
Exerciseur.types_exerciseurs["python"] = ExerciseurRetrocompatiblePython
