from . import Exerciseur

class ExerciseurDockerfile(Exerciseur):
    """
    Une classe pour un exerciseur représenté par un dossier
    contenant un dockerfile.    
    """
    
    def __init__(self, chemin, en_place=True, debug_out=None, **kwargs):
        super().__init__(chemin, en_place=True, debug_out=debug_out, **kwargs)
    
    # Méthodes de Exerciseur

    def métadonnées(self):
        return {}

    def type_exo(self):
        return 'Dockerfile'

    def utiliser_rép_travail(self, rép):
        pass
    
    def copie_source(self):
        pass
    
    def prépare_source(self):
        pass

    def écrit_dockerfile(self):
        pass

Exerciseur.register('Dockerfile', ExerciseurDockerfile)
