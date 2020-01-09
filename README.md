Des outils pour utiliser une image docker par exercice dans l'exerciseur.

Format des exercices
====

Chaque exercice est constitué de:

* une image docker
* un fichier infos.json
	
Le fichier infos.json donne les méta-données sur l'exercice (pour l'affichage par l'exerciseur).

L'image docker a le comportement suivant:

* au boot, écoute sur le port 5678
* à chaque connexion sur le port, lire un objet cbor correspondant à la tentative étudiante
* répondre par un objet json (cbor?) avec le feedback
