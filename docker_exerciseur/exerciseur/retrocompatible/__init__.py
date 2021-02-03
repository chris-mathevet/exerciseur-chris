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


class ExerciseurRetrocompatibleJava(Exerciseur):

    def __init__(self, chemin, en_place=False, debug_out=None, **kwargs):
        super().__init__(chemin, en_place=en_place, debug_out=debug_out)
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
                    contenu_run_py = contenu_run_py.replace("{{%s}}"%elem, self.meta.get(elem))

                out.write(contenu_run_py)
        with open(self.rép_travail + "/Dockerfile", 'w') as out:
            #if self.debug_out:
            #    out = StreamTee(self.debug_out, out)
            contenu_Dockerfile = resources.read_text(__name__, 'Dockerfile.in')
            out.write(contenu_Dockerfile)

    def métadonnées(self):
        return self.meta

    def type_exo(self):
        return self.typeExo

    def prépare_source(self):
        pass


class ExerciseurRetrocompatiblePython(Exerciseur):

    def __init__(self, chemin, en_place=False, debug_out=None, **kwargs):
        super().__init__(chemin, en_place=en_place, debug_out=debug_out)
        self.typeExo="python"
        self.meta = kwargs

    def utiliser_rép_travail(self, chemin):
        self.rép_travail = chemin

    def copie_source(self):
        dest = self.rép_travail
        self.debug("copie des fichiers source dans ", dest)
        shutil.copytree(self.sources, dest)

    def écrit_dockerfile(self):
        from shutil import copyfile
        copyfile(self.rép_travail +"/"+ self.meta.get("fichier_ens"), self.rép_travail +"/code_ens")
        with open(self.rép_travail + "/run.py", 'w') as out:
                #if self.debug_out:
                #    out = StreamTee(self.debug_out, out)
                contenu_run_py = resources.read_text(__name__, 'run_python.py.in')
                contenu_run_py = contenu_run_py.replace("{{typeExo}}", self.typeExo)
                for elem in self.meta:
                    contenu_run_py = contenu_run_py.replace("{{%s}}"%elem, self.meta.get(elem))

                out.write(contenu_run_py)
        with open(self.rép_travail + "/Dockerfile", 'w') as out:
            #if self.debug_out:
            #    out = StreamTee(self.debug_out, out)
            contenu_Dockerfile = resources.read_text(__name__, 'Dockerfile.in')
            out.write(contenu_Dockerfile)

    def métadonnées(self):
        return self.meta

    def type_exo(self):
        return self.typeExo

    def prépare_source(self):
        pass



Exerciseur.types_exerciseurs["java"] = ExerciseurRetrocompatibleJava
Exerciseur.types_exerciseurs["python"] = ExerciseurRetrocompatiblePython
