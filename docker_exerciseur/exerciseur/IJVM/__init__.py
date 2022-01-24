import sys
import os
python_version = sys.version_info
from pathlib import Path
from types import ModuleType
from jinja2 import Environment, FileSystemLoader
if python_version.minor >= 7:
    from importlib import resources
else:
    import importlib_resources as resources
import shutil

from outils_exercices import jacadi
from ..dockerfile import ExerciseurDockerfile
from .. import Exerciseur
import inspect
import uuid

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
        env = Environment(loader=FileSystemLoader(self.rép_travail))
        template = env.get_template("enonce_enseignant.yaml")
        with open(self.rép_travail + "/code_enseignant.yaml", "w", encoding="utf-8") as fichier_code_ens:
            fichier_code_ens.write(template.render())
        numéro_de_série = uuid.uuid4()
        marque_unique = "####" + str(numéro_de_série) + "####"
        contenu_template_etu = "{% extends \"enonce_enseignant.yaml\" %}\n{%block solution %}" + marque_unique + "{% endblock %}"
        path_template_etu = self.rép_travail + "/template_etu.yaml"
        with open(path_template_etu, "w", encoding="utf-8") as fic_template_etu:
            fic_template_etu.write(contenu_template_etu)
        template_etu = env.get_template("template_etu.yaml")
        rendu_template_etu = template_etu.render()
        [prologue, épilogue] = rendu_template_etu.split(marque_unique)
        with open(self.rép_travail + "/prologue_code_etu", "w", encoding="utf-8") as fichier_prologue:
           fichier_prologue.write(prologue)
        with open(self.rép_travail + "/épilogue_code_etu", "w", encoding="utf-8") as fichier_épilogue:
           fichier_épilogue.write(épilogue)
        with resources.path(__name__,"exerciseur.jar") as exerciseur_jar:
           shutil.copyfile(exerciseur_jar, self.rép_travail +"/exerciseur.jar")
        with open(self.rép_travail + "/run.py", 'w') as out:
            contenu_run_py = resources.read_text(__name__, 'testSolution.py.in')
            contenu_run_py = contenu_run_py.replace("{{code_solution}}", str(self.meta.get("codeSolution", "")))
            out.write(contenu_run_py)

    def écrit_dockerfile(self):
        with open(self.rép_travail + "/Dockerfile", 'w') as out:
            if self.avec_openfaas:
                contenu_Dockerfile = resources.read_text(__name__, 'Dockerfile.in')
            else:
                contenu_Dockerfile = resources.read_text(__name__, 'Dockerfile.no_openfaas.in')
            out.write(contenu_Dockerfile)

    def métadonnées(self):
        return self.meta

    def type_exo(self):
        return self.typeExo


Exerciseur.types_exerciseurs["ijvm"] = ExerciseurIJVM
