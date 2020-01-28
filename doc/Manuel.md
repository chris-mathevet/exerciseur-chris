---
title: Manuel de `docker-exerciseur`
author: Florent Becker
listings-no-page-break: true
geometry: margin=3cm
---

Introduction et tutorial
========================

`docker-exerciseur` vous permet de construire une plate-forme d'exerciseurs en réseau. Un *exerciseur* est un dispositif pour permettre à des étudiant·es de s'entrainer à des exercices sur machine, avec une correciton automatique. Il se compose de deux parties: une *interface* web et un *oracle*. L'interface web présente des exercices à résoudre, avec des champs-réponse. Lorsque l'un de ces champs-réponse est validé, l'interface envoie son contenu à l'oracle qui répond par une évaluation de l'exercice, qui est ensuite affichée par l'interface.

`docker-exerciseur` permet de créer les oracles qui évalueront les tentatives envoyées par une interface web. Chaque exercice (ou feuille d'exercices) a son propre oracle sous forme d'une image docker. Les conteneurs issus de cette image écoutent sur le port 5678 des tentatives et renvoient, pour chacune, une évaluation.

Pour installer `docker-exerciseur`, vous pouvez procéder ainsi (depuis la racine du répertoire source de `docker-exerciseur`
```bash
$ python3 setup.py install
$ docker-exerciseur help
```

Assurez-vous que les dépendances de `docker-exerciseur` sont installées (cf. ci-dessous), et considérons un exercice très sophistiqué:

> Écrire un module python contenant une variable globale `a` de valeur 5.

Pour évaluer (sans chercher à donner des indications de qualité) une réponse à cet exercice, on peut utiliser le module de test python suivant (en supposant que le code de la tentative soit dans le module `code_etu`):

```python
import code_etu

def test_a_vaut5():
	assert code_etu.a == 5, "a ne vaut pas 5 dans votre module"
```	

Le fichier `exemples/testsPython/quelques_tests.py` contient sensiblement ce code. Nous pouvons l'utiliser pour construire une image docker qui serve d'oracle pour cet exercice. On utilise à cet effet la commande suivante:

```bash
$ id_image=$(docker-exerciseur construit --type TestsPython --module quelques_tests exemples/testsPython/)
$ echo $id_image
sha256:edf334214dd2bc11589e841f5524226c99a7c62a0d65dbc3cd3621a6c98906fc
```

La réponse de la commande (`sha256:e3f9838f4`…) est l'identifiant de l'image docker qui a été construite. Le script `test_testeur.py` nous permet de tester l'oracle qui vient d'être construit.

```bash
$ cat > /tmp/a.py <<EOF
a = 5
EOF

$ docker-exerciseur test --code-etu /tmp/a.py $id_image | json_pp
{
   "_messages" : [
      "Tous les tests ont réussi, champion·ne!"
   ],
   "_temps" : "0ms",
   "_valide" : true
}
```

On peut ainsi la lancer, puis se connecter sur son port 5678 (ici, on lie ce port 5678 à celui de la machine locale). Ici, on va envoyer comme tentative, la chaîne `'a = 6'`, qui provoque une erreur à l'évaluation. Le préfixe «e» sert à encoder la tentative au format `cbor` pour permettre à l'oracle d'en détecter la fin.

```bash
$ docker run -d -p 5678:5678 $id_image 
$ nc localhost 5678
ea = 6
{"_valide": false, "_messages": ["Exception au chargement de votre code",\
	"name 'abcde' is not defined"], "_temps": "0ms"}
```


Prérequis
---------

Les prérequis de `docker-exerciseur` sont:
	
- python3
- docker
- les modules python suivants: cbor, docker et setuptools

Spécification d'un exerciseur
=============================

Un exerciseur est une image docker. Quand on l'instancie, on obtient un conteneur qui écoute sur le port 5678. Les données envoyées sur le port 5678 sont interprétées comme des tentatives encodées en `cbor`. À chaque tentative, l'exerciseur répond par une évaluation. Cette évaluation est un objet `json` quelconque. Si elle contient un champ "_valide", sa valeur doit être booléenne et indique si la tentative est considérée comme correcte.

Construire un exerciseur
========================

La commande `docker-exerciseur construit` permet de construire un exerciseur. Son argument est le chemin d'un dossier ou d'un fichier tar (à défaut, le dossier courant) qui constient les sources de l'exerciseur. À quel format sont les sources de l'exerciseur? Il y a plusieurs types de sources possibles, l'argument `--type` de `docker-exerciseur construit` permet d'en sélectionner un. La table ci-dessous résume les types d'exercices possibles. Les exemples se trouvent dans le répertoire `exemples` de la distriubtion source.

| Type | Contenu du répertoire source | Exemple |
| -----| ---------------------------- | ------- |
| `Dockerfile` | Un dossier contenant un Dockerfile | dockerfile_true |
| `DémonPy` | Un script python qui écoute des tentatives sur le port 5678 | ToujoursContent |
| `PackagePy` | Un package python contenant une classe avec une méthode `évalue` | ClasseToujoursContent |
| `TestsPy` | Un module python qui importe une tentative et lance des tests | testsPython |
| `Jacadi` | Un module python avec fonction et des entrées de test | oldSchoolCool |


Les exerciseurs `Dockerfile`
---------------------------

Un exerciseur `Dockerfile` se construit à partir d'un dossier contenant un Dockerfile. Ce Dockerfile doit produire un exerciseur au sens de la section ci-dessus. Essentiellement, la commande `exerciseur-docker --type Dockerfile dossier` est équivalente à `docker build dossier`.

Les exerciseurs `DémonPy`
-------------------------

Un exerciseur `DémonPy` est composé d'un dossier contenant un démon écrit en python. L'exerciseur construit par `DémonPy` exécute le démon `daemon.py` fourni dans le dossier source (sans arguments). Ce démon doit écouter sur le port 5678 et évaluer les tentatives qu'il y reçoit.

Si un fichier `requirements.txt` existe dans le dossier source, les package python correspondants seront installés. Si un `Dockerfile` existe, il sera utilisé comme base avant d'exécuter l'installation du démon. Ce Dockerfile doit donc fournir `python3` et `pip`.

Les exerciseurs `PackagePy`
-------------------------

Un exerciseur `PackagePy` est composé d'un package python contenant un module (nommé par défaut `exerciseur`) contenant une classe `SessionÉtudiante` (donnée par l'argument `--classe NomClasse`). Cette classe doit contenir une méthode `évalue` qui prend en argument une chaine correspondant au contenu de la tentative (décodée depuis le message `cbor` sur la socket) et renvoie une évaluation en `json`.


Les exerciseurs `TestsPy`
-------------------------

Un exerciseur `TestsPy` est composé d'un package python avec un module (dont le nom est donné par l'argument `--module nom_module`) contenant des fonctions `test_*`. Chacune de ces fonctions est un test, qui s'exécute sans lever d'exception si la tentative est correcte. Le module accède à la tentative qui a été soumise en important le module `code_etu`.

Les exerciseurs `Jacadi`
-----------------------

Un exerciseur `Jacadi` est composé d'un package python. Celui-ci contient un module (dont le nom est donné par l'argument `--module nom_module`). Ce module doit contenir une fonction marquée par le décorateur `@solution`, ainsi que deux listes `entrees_visibles` et `entrees_invisibles`.

Tester un exerciseur
====================


Interface python
================

Il est possible d'utiliser `docker-exerciseur` depuis du code python. Il faut pour celà bien entendu importer soit le module de test, soit le module de construction:
```python
import docker_exerciseur.constructeur
import docker_exerciseur.testeur
```

Utilisation du constructeur
----

Le constructeur s'utilise par la fonction `docker_exerciseur.constructeur.construit_exerciseur`:
```python
def construit_exerciseur(type_ex, dossier_source, verbose, **kwargs):
    """
    Construit un exerciseur. Les arguments correspondent à ceux de `docker-exerciseur construit`

    @param type_ex: le type d'exerciseur, parmi "DémonPy", "PackagePy", "TestsPy", "Dockerfile" ou "Jacadi"
    @param source: un objet contenant les sources de l'exerciseur: soit un `FluxTar`, soit un `DossierSource`
    @param verbose: un booléen, vrai pour afficher plus d'informations sur sys.stderr
    @param kwarg: un dictionnaire qui sert à donner des arguments supplémentaires en fonction de `type_ex`.
    - pour PackagePy, `module="nom_module"` indique quel module contient la classe exerciseur et `classe="NomClasse"` le nom de cette classe
    - pour TestsPy, `module="nom_module"` indique quel module contient les tests
    - pour Jacadi, `module="mod_ens"` indique quel module contient le code enseignant.

    @return l'idententifiant de l'image construite pour cet exerciseur.
    """
```

Les objets "source" peuvent être construits soit par `docker_exerciseur.construit_exerciseur.DossierSource(chemin)`, soit par `docker_exerciseur.construit_exerciseur.FluxTar(open('toto.tar'))`, soit par `docker_exerciseur.construit_exerciseur.FluxTar(b'contenu_de_toto.tar'))`.

Utilisation du testeur
-----

Le testeur s'utilise par la fonction `docker_exerciseur.testeur.test_nouveau_container`:

```python
def test_nouveau_container(exerciseur: Union[str, docker.models.images.Image],
                           code_etu: Union[str, bytes],
                           verbose: bool,
                           docker_client=None):
    """
    Test une tentative étudiante dans un nouveau container pour un exerciseur.

    @param exerciseur: l'exerciseur à utiliser, donné sous forme soit d'un identifiant d'image, soit d'un objet image de la bibliothèque docker
    @param code_etu: une chaîne de caractères contenant le code soumis par l'étudiant·e
    @param verbose: indique si on doit se répandre sur sys.stderr
    @param docker_client: un objet client-docker à réutiliser (None pour utiliser docker.from_env())

    @return le dictionnaire d'évaluation de la tentative (à sérialiser en json)
    """
```


Installer une ferme d'exerciseurs
=================================
