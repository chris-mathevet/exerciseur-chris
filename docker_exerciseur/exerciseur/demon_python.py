import shutil
import os

from . import Exerciseur
from ..stream_tee import StreamTee

class ExerciseurDémonPython(Exerciseur):
    """
    Un exerciseur pour un testeur écrit en python (le testeur
    doit implémenter un démon qui écoute des tentatives en http sur le port 8080).

    @param dossier_code: un dossier contenant le code du démon
    """

    def __init__(self, dossier_code, nom_démon='daemon.py', en_place=False, debug_out=None, **kwargs):
        super().__init__(dossier_code, en_place=en_place, debug_out=debug_out, **kwargs)
        self.nom_démon = nom_démon
        self.rép_travail = None
        self.dockerfile = None
        self.position_démon = '.'
        self.debug_out = debug_out

    def utiliser_rép_travail(self, chemin):
        self.rép_travail = chemin

    def copie_source(self):
        dest = self.rép_travail
        self.debug("copie des fichiers source dans ", dest)
        shutil.copytree(self.sources, dest)

    def prépare_source(self):
        pass

    def écrit_dockerfile(self):
        out = open(self.rép_travail + "/Dockerfile", 'w')
        self.debug("----------")
        self.debug("Dockerfile")
        self.debug("----------")
        if self.debug_out:
            out = StreamTee(self.debug_out, out)
        # print("FROM python:alpine3.8", file=out)
        # print("COPY", self.position_démon, " /exerciseur", file=out)
        # print("WORKDIR /exerciseur", file=out)
        # if os.path.isfile(self.rép_travail + "/requirements.txt"):
        #     print("RUN pip install -r requirements.txt", file=out)
        # print("EXPOSE 8080", file=out)
        # print("CMD exec python " + self.nom_démon, file=out)
        print("FROM openfaas/of-watchdog:0.7.6 as watchdog", file=out)
        print("FROM python:alpine3.8", file=out)
        print("COPY --from=watchdog /fwatchdog /usr/bin/fwatchdog", file=out)
        print("RUN chmod +x /usr/bin/fwatchdog", file=out)
        print("COPY", self.position_démon, " /exerciseur", file=out)
        print("WORKDIR /exerciseur", file=out)
        if os.path.isfile(self.rép_travail + "/requirements.txt"):
            print("RUN pip install -r requirements.txt", file=out)
        print("ENV fprocess=\"python3 /exerciseur/" + self.nom_démon +"\"", file=out)
        print("ENV upstream_url=\"http://127.0.0.1:8082\"", file=out)
        print("ENV mode=\"http\"", file=out)
        print("EXPOSE 8080", file=out)
        print("ENV exec_timeout=\"10s\"", file=out)
        print('CMD ["fwatchdog"]', file=out)

    def métadonnées(self):
        return {
            'nom_démon': self.nom_démon,
            }

    def type_exo(self):
        return 'DémonPython'

Exerciseur.types_exerciseurs['DémonPython'] = ExerciseurDémonPython
