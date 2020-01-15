% Manuel de `docker-exerciseur`

Introduction et tutorial
========================

`docker-exerciseur` vous permet de construire une plate-forme d'exerciseurs en réseau. Un *exerciseur* est un dispositif pour permettre à des étudiant·es de s'entrainer à des exercices sur machine, avec une correciton automatique. Il se compose de deux parties: une *interface* web et un *oracle*. L'interface web présente des exercices à résoudre, avec des champs-réponse. Lorsque l'un de ces champs-réponse est validé, l'interface envoie son contenu à l'oracle qui répond par une évaluation de l'exercice, qui est ensuite affichée par l'interface.

`docker-exerciseur` permet de créer les oracles qui évalueront les tentatives envoyées par une interface web. Chaque exercice (ou feuille d'exercices) a son propre oracle sous forme d'une image docker. Les conteneurs issus de cette image écoutent sur le port 5678 des tentatives et renvoient, pour chacune, une évaluation.

Assurez-vous que les dépendances de `docker-exerciseur` sont installées (cf. ci-dessous), et considérons un exercice très sophistiqué:

> Écrire un module python contenant une variable globale `a` de valeur 5.

Pour évaluer (de façon binaire) une réponse à cet exercice, on peut utiliser le module de test python suivant (en supposant que le code de la tentative soit dans le module `code_etu`):

```python
import code_etu

def test_a_vaut5():
	assert code_etu.a == 5, "a ne vaut pas 5 dans votre module"
```	

Le fichier `exemples/testsPython/quelques_tests.py` contient sensiblement ce code. Nous pouvons l'utiliser pour construire une image docker qui serve d'oracle pour cet exercice. On utilise à cet effet la commande suivante:

```bash
$ id_image=$(python3 construit_exerciseur/constructeur.py \
	--dossier-python exemples/testsPython/ \
	--module quelques_tests \
	--type PythonTests)
$ echo $id_image
sha256:edf334214dd2bc11589e841f5524226c99a7c62a0d65dbc3cd3621a6c98906fc
```

La réponse de la commande (`sha256:e3f9838f4`…) est l'identifiant de l'image docker qui a été construite. Le script `test_testeur.py` nous permet de tester l'oracle qui vient d'être construit.

```bash
$ cat > /tmp/a.py <<EOF
a = 5
EOF

$ python3 test_testeur.py --code-etu /tmp/a.py --nom-image $id_image | json_pp
{
   "_messages" : [
      "Tous les tests ont réussi, champion·ne!"
   ],
   "_temps" : "0ms",
   "_valide" : true
}
```

On peut ainsi la lancer, puis se connecter sur son port 5678 (ici, on lie ce port 5678 à celui de la machine locale). Ici, on va envoyer comme tentative, la chaîne `'abcde'`, qui provoque une erreur à l'évaluation. Le préfixe «e» sert à encoder la tentative au format `cbor` pour permettre à l'oracle d'en détecter la fin.

```bash
$ docker run -d -p 5678:5678 $id_image 
$ nc localhost 5678
eabcde
{"_valide": false, "_messages": ["Exception au chargement de votre code", "name 'abcde' is not defined"], "_temps": "0ms"}
```


Prérequis
---------

Les prérequis de `docker-exerciseur` sont:
	
- python3
- docker
- les modules python suivants: cbor, docker et setuptools

Construire un exerciseur
========================


Tester un exerciseur
====================


Installer une ferme d'exerciseurs
=================================
