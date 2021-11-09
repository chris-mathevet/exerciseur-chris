import tempfile
import subprocess
from nose2.tools import params

from .exerciseur import *
from .testeur import *
from . import constructeur


code_etu = '''
  .constant
  OBJREF 42
  .end-constant

  .method mulrec( x,y )
  .var
  a
  b
  .end-var
  ILOAD x
  DUP
  BIPUSH 1
  ISUB
  ISTORE a
  IFEQ end
  BIPUSH 40
  ILOAD a
  ILOAD y
  INVOKEVIRTUAL mulrec
  ILOAD y
  IADD
  IRETURN
  end: BIPUSH 0
  IRETURN
  .end-method

  .main
  .var
  a
  b
  resultat
  total
  .end-var

  start:        BIPUSH 02
  BIPUSH 40
  BIPUSH 02
  BIPUSH 05
  INVOKEVIRTUAL mulrec
  ISTORE resultat
  ILOAD resultat
  BIPUSH 30
  IADD
  .end-main
'''

import os

exemples = (
    {'type_ex': 'ijvm',
     'chemin_source': os.path.abspath('exemples/ijvm'),
     'métadonnées' : { 'codeSolution': 65444 },
     'tentatives' : [
         {
             'entree' : { 'code_etu':code_etu },
             'réponse' : 
             {
                '_valide': True, 
                'feedbacks_html': '<div><p>Exercice réussi!</p><p>Votre code retour est : 65444</p></div>'}
         },
     ],
       'métadonnées_attendues' :{ 'codeSolution': 65444 }
    },
)

@params(*exemples)
def test_construit(e):
    Classe = Exerciseur.types_exerciseurs[e['type_ex']]
    ed = Classe(e['chemin_source'], **e['métadonnées'])
    ed.construire()


@params(*exemples)
def test_réponse_openfaas(e):
    Classe = Exerciseur.types_exerciseurs[e['type_ex']]
    ed = Classe(e['chemin_source'], **e['métadonnées'])
    sha = ed.construire()
    for t in e['tentatives']:
        éval_tentative = éprouve_dans_openfaas(sha.split(':')[1][:62], **t['entree'])
        assert éval_tentative == t['réponse'], ('réponse obtenue:' + str(éval_tentative))



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
