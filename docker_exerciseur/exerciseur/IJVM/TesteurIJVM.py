__author__ = 'julien'
from ..Testeur import Testeur
from string import Template
import os
import shutil



class TesteurIJVM(Testeur):
    
    nom = "IJVM"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def writeTestFiles(self, directory):

        with open(os.path.join(directory, "enonce_enseignant.yaml"), "w", encoding="utf-8") as yaml_test:
            yaml_test.write(self.codeTest.decode())

        with open(os.path.join(directory, "solution_etudiant.yaml"), "w", encoding="utf-8") as solution_etudiant:
            solution_etudiant.write(self.codeATester)
        
        with open(os.path.join(directory, "makefile"), "w", encoding="utf-8") as file:
            extra = self.metainfos.get("extra_yaml",{}) if self.metainfos else {}
            code = extra.get("codeSolution","2") 
            file.write("all:\n\tpython3 testSolution.py -t enonce_enseignant.yaml -c \"%s\" solution_etudiant.yaml\n\ninfos:\n\techo {}"%code)
        shutil.copyfile(os.path.join(os.path.dirname(__file__), "testSolution.py"),
                        os.path.join(directory, "testSolution.py"))

        shutil.copyfile(os.path.join(os.path.dirname(__file__), "exerciseur.jar"),
                        os.path.join(directory, "exerciseur.jar"))
