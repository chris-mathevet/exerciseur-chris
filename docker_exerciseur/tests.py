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

code_maj_paire_faux = '''
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
            cpt+=2
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

code_maj_paire_manquants = '''
def pairesPlusNombreuxQuImpairsOuPeutÊtreÉgalQuiSait(liste):
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


code_maj_paire_exception = '''
def fonction_1(liste):
    raise ValueError("fallait pas me chercher")

def pairesMajoritaires(liste):
    return fonction_1(liste)
'''


import os

exemples = (
    {'type_ex': 'DémonPython',
     'chemin_source': os.path.abspath('exemples/ToujoursContent'),
     'métadonnées' : {},
     'tentatives' : [
         {
             'code_etu': 'coucou',
             'réponse' :              {
                 "_valide": True,
                 "_messages": ["T'es un·e champion·ne", "C'est exactement 'b'coucou'' que j'attendais"],
                 'feedbacks_html': "<div>\n<p>Exercice réussi!</p>\n<ul>\n<li>T'es un·e champion·ne</li>\n<li>C'est exactement 'b'coucou'' que j'attendais</li>\n</ul>\n</div>\n"
             }
         }
     ]
    },
    {'type_ex': 'DémonPython',
     'chemin_source': 'exemples/ToujoursContent',
     'métadonnées' : {},
     'tentatives' : [
         {
             'code_etu': 'coucou',
             'réponse' :
             {
                 "_valide": True,
                 "_messages": ["T'es un·e champion·ne", "C'est exactement 'b'coucou'' que j'attendais"],
                 'feedbacks_html': "<div>\n<p>Exercice réussi!</p>\n<ul>\n<li>T'es un·e champion·ne</li>\n<li>C'est exactement 'b'coucou'' que j'attendais</li>\n</ul>\n</div>\n"
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
             'réponse' : {'_valide': True,
                          '_messages': ["T'es un·e champion·ne", "C'est exactement 'b'coucou'' que j'attendais"],
                          '_temps': '0ms',
                          'feedbacks_html': "<div>\n<p>Exercice réussi!</p>\n<ul>\n<li>T'es un·e champion·ne</li>\n<li>C'est exactement 'b'coucou'' que j'attendais</li>\n</ul>\n</div>\n"
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
             'réponse' : {'_valide': True,
                          '_messages': ["T'es un·e champion·ne", "C'est exactement 'b'coucou'' que j'attendais"],
                          '_temps': '0ms',
                          'feedbacks_html': "<div>\n<p>Exercice réussi!</p>\n<ul>\n<li>T'es un·e champion·ne</li>\n<li>C'est exactement 'b'coucou'' que j'attendais</li>\n</ul>\n</div>\n"
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
                 '_temps': '0ms',
                 'feedbacks_html': "<div>\n<p>Exercice réussi!</p>\n<ul>\n<li>Tous les tests ont réussi, champion·ne!</li>\n</ul>\n</div>\n"
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
                 '_temps': '0ms',
                 'feedbacks_html': "<div>\n<p>Exercice réussi!</p>\n<ul>\n<li>Tous les tests ont réussi, champion·ne!</li>\n</ul>\n</div>\n"
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
                 '_temps': '0ms',
                 'feedbacks_html': "<div>\n<p>Exercice réussi!</p>\n<ul>\n<li>Tous les tests ont réussi, champion·ne!</li>\n</ul>\n</div>\n"
             }
         },
         {
             'code_etu': code_maj_paire_faux,
             'réponse' : {'_valide': False, '_messages': ["Erreur, sur l'entrée ([-5, 4, 3],), vous retournez 0 au lieu de -1."], 'feedbacks_html': "<div>\n<p>Il y a une erreur</p>\n<ul>\n<li>Erreur, sur l'entrée ([-5, 4, 3],), vous retournez 0 au lieu de -1.</li>\n</ul>\n</div>\n"}
         },
         {
             'code_etu': code_maj_paire_manquants,
             'réponse' : {'_valide': False,
                          '_messages': ['Vous ne fournissez pas la fonction pairesMajoritaires demandée'],
                          'feedbacks_html': '<div>\n<p>Il y a une erreur</p>\n<ul>\n<li>Vous ne fournissez pas la fonction pairesMajoritaires demandée</li>\n</ul>\n</div>\n'}
         },
         {
             'code_etu': code_maj_paire_exception,
             'réponse' : {'_valide': False,
                          '_messages': ["Erreur, sur l'entrée ([],), vous levez ValueError('fallait pas me chercher') au lieu de renvoyer 0."],
                          'feedbacks_html': "<div>\n<p>Il y a une erreur</p>\n<ul>\n<li>Erreur, sur l'entrée ([],), vous levez ValueError('fallait pas me chercher') au lieu de renvoyer 0.</li>\n</ul>\n</div>\n"}
         }
     ]
    }
)

@params(*exemples)
def test_empaquète_dépaquete(e):
    ed = Exerciseur.avec_type(e['chemin_source'], e['type_ex'], **e['métadonnées'])
    paquet = ed.empaquète()
    sha_ref = ed.construire()
    with paquet as exerciseur_dépaqueté:
        sha_empaquète_dépaquète = exerciseur_dépaqueté.construire()
    assert sha_ref == sha_empaquète_dépaquète

    
@params(*exemples)
def test_empaquète_dépaquete_cbor(e):
    ed = Exerciseur.avec_type(e['chemin_source'], e['type_ex'], **e['métadonnées'])
    sha_ref = ed.construire()
    paquet = ed.empaquète()
    cbor = paquet.vers_cbor()
    paquet2 = PaquetExercice.depuis_cbor(cbor)
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
        if sys.version_info.minor >= 7:
            diff = subprocess.run(
                ["diff" ,"-u", source_dir_dpq, e['chemin_source']],
                capture_output=True)
        else:
            from subprocess import PIPE
            diff = subprocess.run(
                ["diff" ,"-u", source_dir_dpq, e['chemin_source']], stdout=PIPE)
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
def test_testeur_détruit_container(e):
    docker_client = docker.from_env()
    n_containers_avant = len(docker_client.containers.list(all=True))
    Classe = Exerciseur.types_exerciseurs[e['type_ex']]
    ed = Classe(e['chemin_source'], **e['métadonnées'])
    sha = ed.construire()
    for t in e['tentatives']:
        éval_tentative = éprouve_dans_nouveau_container(sha, t['code_etu'], docker_client=docker_client)
    n_containers_après = len(docker_client.containers.list(all=True))
    assert n_containers_avant == n_containers_après


@params(*exemples)
def test_construit_exerciseur(e):
    Classe = Exerciseur.types_exerciseurs[e['type_ex']]
    ed = Classe(e['chemin_source'], **e['métadonnées'])
    sha = ed.construire()
    sha_bis = constructeur.construit_exerciseur(e['type_ex'], e['chemin_source'], False, **e['métadonnées'])
    assert sha == sha_bis
