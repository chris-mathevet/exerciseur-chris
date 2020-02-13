import tempfile
import subprocess
from nose2.tools import params

from .exerciseur import *
from .testeur import *
from . import constructeur

code_maj_paire = '''
def pairesMajoritaires(liste):
    """
    permet de savoir si une liste d'entiers contient une majorité 
    de nombres paires ou non
    paramètre: liste une liste d'entiers
    resultat: 1 si les paires sont majoritaires, -1 si ce sont les impaires
              0 en cas d'égalité
    """
    # je choisis for elem in liste car je dois parcourir tous les éléments
    # d'une seule liste pour obtenir le résultat
    cpt=0
    for nb in liste: 
    #invariant: cpt contient la différence entre le nombre d'entiers paires et
    #           et le nombres d'entiers impaires déjà énumérés
        if nb%2==0:
            cpt+=1
        else:
            cpt-=1
    if cpt>0:
        res=1
    elif cpt<0:
        res=-1
    else:
        res=0
    return res
'''

exemples = (
    {'type_ex': 'DémonPython',
     'chemin_source': 'exemples/ToujoursContent',
     'métadonnées' : {},
     'tentatives' : [
         {
             'code_etu': 'coucou',
             'réponse' : {
                 '_valide': True,
                 '_messages': ["T'es un·e champion·ne", "C'est exactement 'b'coucou'' que j'attendais"],
                 '_temps': '0ms'
             }
         }
     ]
    },
    {'type_ex': 'Dockerfile',
     'chemin_source': 'exemples/dockerfile_true',
     'métadonnées' : {},
     'tentatives' : [
         {
             'code_etu': 'coucou',
             'réponse' : {
                 '_valide': True,
                 '_messages': ["T'es un·e champion·ne", "C'est exactement 'b'coucou'' que j'attendais"],
                 '_temps': '0ms'
             }
         }
     ]
    },
    {'type_ex': 'PackagePython',
     'chemin_source': 'exemples/ClasseToujoursContente',
     'métadonnées' : {},
     'tentatives' : [
         {
             'code_etu': 'coucou',
             'réponse' : {
                 '_valide': True,
                 '_messages': ["T'es un·e champion·ne", "C'est exactement 'b'coucou'' que j'attendais"],
                 '_temps': '0ms'
             }
         }
     ]
    },
    {'type_ex': 'TestsPython',
     'chemin_source': 'exemples/testsPython',
     'métadonnées' : { 'nom_module': 'quelques_tests'},
     'tentatives' : [
         {
             'code_etu': 'a = 5',
             'réponse' : {
                 '_valide': True,
                 '_messages': ["Tous les tests ont réussi, champion·ne!"],
                 '_temps': '0ms'
             }
         }
     ]
    },
    {'type_ex': 'Jacadi',
     'chemin_source': 'exemples/jacadiMajoritePaire',
     'métadonnées' : { 'fichier_ens': 'majoritePaire.py'},
     'tentatives' : [
         {
             'code_etu': code_maj_paire,
             'réponse' : {
                 '_valide': True,
                 '_messages': ["Tous les tests ont réussi, champion·ne!"],
                 '_temps': '0ms'
             }
         }
     ]
    },
    {'type_ex': 'Jacadi',
     'chemin_source': 'exemples/jacadiMajoritePaire',
     'métadonnées' : {},
     'tentatives' : [
         {
             'code_etu': code_maj_paire,
             'réponse' : {
                 '_valide': True,
                 '_messages': ["Tous les tests ont réussi, champion·ne!"],
                 '_temps': '0ms'
             }
         }
     ]
    }
)

@params(*exemples)
def test_empaquète_dépaquete(e):
    Classe = Exerciseur.types_exerciseurs[e['type_ex']]
    ed = Classe(e['chemin_source'], **e['métadonnées'])
    paquet = ed.empaquète()
    sha_ref = ed.construire()
    with paquet as exerciseur_dépaqueté:
        sha_empaquète_dépaquète = exerciseur_dépaqueté.construire()
    assert sha_ref == sha_empaquète_dépaquète


@params(*exemples)
def test_empaquète_sérialise_désérialise_dépaquete(e):
    Classe = Exerciseur.types_exerciseurs[e['type_ex']]
    ed = Classe(e['chemin_source'], **e['métadonnées'])
    paquet = ed.empaquète()
    d = paquet.to_dict()
    sha_ref = ed.construire()
    paquet_déser = PaquetExercice.from_dict(d)
    with paquet_déser as exerciseur_dépaqueté:
        sha_empaquète_dépaquète = exerciseur_dépaqueté.construire()
    assert sha_ref == sha_empaquète_dépaquète

    
@params(*exemples)
def test_construit(e):
    Classe = Exerciseur.types_exerciseurs[e['type_ex']]
    ed = Classe(e['chemin_source'], **e['métadonnées'])
    ed.construire()

@params(*exemples)
def test_dépaquète_source(e, verbose=False):
    Classe = Exerciseur.types_exerciseurs[e['type_ex']]
    ed = Classe(e['chemin_source'], **e['métadonnées'])
    p = ed.empaquète()
    with p as edx:
        source_dir_dpq = edx.sources
        diff = subprocess.run(
            ["diff" ,"-u", source_dir_dpq, e['chemin_source']],
            capture_output=True)
        if verbose:
            print(diff.stdout)
        assert diff.returncode == 0

@params(*exemples)
def test_verbose_change_rien(e):
    Classe = Exerciseur.types_exerciseurs[e['type_ex']]
    ed = Classe(e['chemin_source'], **e['métadonnées'])
    sha_ref = ed.construire()
    with open('/dev/null', 'w') as dev_null:
        edv = Classe(e['chemin_source'], **e['métadonnées'], debug_out=dev_null)
        sha_verbose = edv.construire()
        assert sha_ref == sha_verbose
    
@params(*exemples)
def test_réponse_docker(e):
    Classe = Exerciseur.types_exerciseurs[e['type_ex']]
    ed = Classe(e['chemin_source'], **e['métadonnées'])
    sha = ed.construire()
    for t in e['tentatives']:
        éval_tentative = éprouve_dans_nouveau_container(sha, t['code_etu'])
        assert éval_tentative == t['réponse'], ('réponse obtenue:' + str(éval_tentative))

@params(*exemples)
def test_construit_exerciseur(e):
    Classe = Exerciseur.types_exerciseurs[e['type_ex']]
    ed = Classe(e['chemin_source'], **e['métadonnées'])
    sha = ed.construire()
    sha_bis = constructeur.construit_exerciseur(e['type_ex'], e['chemin_source'], False, **e['métadonnées'])
    assert sha == sha_bis
