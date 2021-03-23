import tempfile
import subprocess
from nose2.tools import params

from .exerciseur import *
from .testeur import *
from . import constructeur
import os

exemples = (
    {'type_ex': 'java',
     'chemin_source': os.path.abspath('exemples/java'),
     'métadonnées' : { 'nom_classe_test': 'MaClasseTest', 'nom_classe_etu': 'MaClasse' },
     'tentatives' : [
         {
             'code_etu': '''public class Truc{}''',
             'réponse' :              {
                 "_valide": False,
                 "_messages": {"Erreur de compilation dans le fichier MaClasse.java": ["ligne 1\nclass Truc is public, should be declared in a file named Truc.java"]},
                 "feedbacks_html": "<h1>Erreur de compilation dans le fichier MaClasse.java</h1><div>ligne 1\nclass Truc is public, should be declared in a file named Truc.java</div>"
             }
         }
     ],
       'métadonnées_attendues' :{ 'nom_classe_test': 'MaClasseTest', 'nom_classe_etu': 'MaClasse' }
    },
    {'type_ex': 'python',
     'chemin_source': os.path.abspath('exemples/jacadiMajoritePaire'),
     'métadonnées' : { 'fichier_ens': 'majoritePaire.py' },
     'tentatives' : [
         {
             'code_etu': '''def min(x,y):
                                return x
                         ''',
             'réponse' :{'_valide': False,
                        '_messages': {"Vous n'avez pas respecté l'énoncé": ['Votre programme doit contenir une fonction pairesMajoritaires']},
                        '_temps': None,
                        'feedbacks_html': "<h1>Vous n'avez pas respecté l'énoncé</h1><div>Votre programme doit contenir une fonction pairesMajoritaires</div>"
                        }
         }
     ],
     'métadonnées_attendues' :{
                               'fichier_ens': 'majoritePaire.py',
                               'nom_solution': 'pairesMajoritaires',
                               'entrees_visibles': [([],), ([-5, 4, 3],), ([-12, 4, 3],)],
                               'entrees_invisibles': [([14, 23, 10, 8, 7],), ([-4, 1, -4, 3, 8],)],
                               'sorties_visibles': [(([],), 0), (([-5, 4, 3],), -1), (([-12, 4, 3],), 1)],
                               'sorties_invisibles': [(([14, 23, 10, 8, 7],), 1), (([-4, 1, -4, 3, 8],), 1)],
                               'arguments': ['liste']
                               }

    },
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
     ],
     'métadonnées_attendues' :{'nom_démon': 'daemon.py'}
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
     ],
      'métadonnées_attendues' :{'nom_démon': 'daemon.py'}
    },
    {'type_ex': 'Dockerfile',
     'chemin_source': 'exemples/dockerfile_true',
     'métadonnées' : {},
     'tentatives' : [
         {
             'code_etu': 'coucou',
             'réponse' : {'_valide': True,
                          '_messages': ["T'es un·e champion·ne", "C'est exactement 'b'coucou'' que j'attendais"],
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
                          'feedbacks_html': "<div>\n<p>Exercice réussi!</p>\n<ul>\n<li>T'es un·e champion·ne</li>\n<li>C'est exactement 'b'coucou'' que j'attendais</li>\n</ul>\n</div>\n"
             }
         }
     ],
      'métadonnées_attendues': {'nom_module': 'exerciseur', 'nom_classe': 'ToujoursContent'}
    },
    {'type_ex': 'TestsPython',
     'chemin_source': 'exemples/testsPython',
     'métadonnées' : { 'nom_module': 'quelques_tests'},
     'tentatives' : [
         {
             'code_etu': 'a = 5',
             'réponse' : {'_valide': True,
             '_messages': ['Vous passez avec brio le test 1', 'Tous les tests ont réussi, champion·ne!'],
             'feedbacks_html': '<div>\n<p>Exercice réussi!</p>\n<ul>\n<li>Vous passez avec brio le test 1</li>\n<li>Tous les tests ont réussi, champion·ne!</li>\n</ul>\n</div>\n'}
          }
     ],
    'métadonnées_attendues': { 'nom_module': 'quelques_tests'}
    },
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
def test_réponse_openfaas(e):
    Classe = Exerciseur.types_exerciseurs[e['type_ex']]
    ed = Classe(e['chemin_source'], **e['métadonnées'])
    sha = ed.construire()
    for t in e['tentatives']:
        éval_tentative = éprouve_dans_openfaas(sha.split(':')[1][:62], t['code_etu'])
        assert éval_tentative == t['réponse'], ('réponse obtenue:' + str(éval_tentative))


# @params(*exemples)
# def test_réponse_docker(e):
#     Classe = Exerciseur.types_exerciseurs[e['type_ex']]
#     ed = Classe(e['chemin_source'], **e['métadonnées'])
#     sha = ed.construire()
#     for t in e['tentatives']:
#         éval_tentative = éprouve_dans_nouveau_container(sha, t['code_etu'])
#         assert éval_tentative == t['réponse'], ('réponse obtenue:' + str(éval_tentative))

# @params(*exemples)
# def test_testeur_détruit_container(e):
#     docker_client = docker.from_env()
#     n_containers_avant = len(docker_client.containers.list(all=True))
#     Classe = Exerciseur.types_exerciseurs[e['type_ex']]
#     ed = Classe(e['chemin_source'], **e['métadonnées'])
#     sha = ed.construire()
#     for t in e['tentatives']:
#         éval_tentative = éprouve_dans_nouveau_container(sha, t['code_etu'], docker_client=docker_client)
#     n_containers_après = len(docker_client.containers.list(all=True))
#     assert n_containers_avant == n_containers_après


@params(*exemples)
def test_construit_exerciseur(e):
    Classe = Exerciseur.types_exerciseurs[e['type_ex']]
    ed = Classe(e['chemin_source'], **e['métadonnées'])
    sha = ed.construire()
    sha_bis = constructeur.construit_exerciseur(e['type_ex'], e['chemin_source'], False, **e['métadonnées'])
    assert sha == sha_bis


@params(*exemples)
def test_metadonnees(e):
    Classe = Exerciseur.types_exerciseurs[e['type_ex']]
    ed = Classe(e['chemin_source'], **e['métadonnées'])
    sha = ed.construire()
    assert ed.meta == e.get("métadonnées_attendues", {}), "Métadonnées obentenues :" + str(ed.métadonnées()) + "alors qu'on attendait " + str(e.get("métadonnées_attendues", {}))
