import tempfile
import subprocess
from nose2.tools import params

from .exerciseur import *
from .testeur import *
from . import constructeur


code_etu_Personnage = '''
class Personnage{

  private String nom;
  private int barbe;
  private int taille;
  Personnage(String a, int barbe, int taille){
  	this.nom = a;
    this.barbe = barbe;
    this.taille = taille;
  }

  public int tailleOreilles(){
    return this.taille;
  }

  public int getBarbe(){
  	return this.barbe;
  }
  public String getNom(){
	return this.nom;
  }
}
'''

code_etu_Personnage_1 = '''
public class Personnage{

  	private String nom;
    private int barbe;
  	private int taille;

  	public Personnage(String n, int b, int t){
    }
}
'''

import os

exemples = (
    {'type_ex': 'java',
     'chemin_source': os.path.abspath('exemples/java'),
     'métadonnées' : { 'nom_classe_test': 'TestPersonnage', 'nom_classe_etu': 'Personnage' },
     'tentatives' : [
         {
             'entree' : { 'code_etu':code_etu_Personnage },
             'réponse' :              {
                 "_valide": True,
                 "_messages": {},
                 "feedbacks_html": "<h1> Félicitations ! </h1>"
             }
         },
         {
             'entree' : { 'code_etu':code_etu_Personnage_1 },
             'réponse' :{
                   '_messages': {'Erreur de compilation dans le fichier TestPersonnage.java': ['ligne 14\ncannot find symbol\n  symbol:   method getNom()\n  location: variable p of type Personnage', 'ligne 15\ncannot find symbol\n  symbol:   method getBarbe()\n  location: variable p of type Personnage', 'ligne 16\ncannot find symbol\n  symbol:   method tailleOreilles()\n  location: variable p of type Personnage']},
                   '_valide': False,
                   'feedbacks_html': '<h1>Erreur de compilation dans le fichier TestPersonnage.java</h1><div>ligne 14\ncannot find symbol\n  symbol:   method getNom()\n  location: variable p of type Personnage</div><div>ligne 15\ncannot find symbol\n  symbol:   method getBarbe()\n  location: variable p of type Personnage</div><div>ligne 16\ncannot find symbol\n  symbol:   method tailleOreilles()\n  location: variable p of type Personnage</div>'
                }
         },

     ],
       'métadonnées_attendues' :{ 'nom_classe_test': 'TestPersonnage', 'nom_classe_etu': 'Personnage' }
    },
)

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
