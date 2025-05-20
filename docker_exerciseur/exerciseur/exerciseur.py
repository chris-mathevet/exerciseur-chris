from abc import ABC, abstractmethod, ABCMeta

from typing import Dict
import docker
import tempfile
import os
import sys
import io
import tarfile
from pathlib import Path
from types import ModuleType
import cbor
import requests, json

# from ..stream_tee import StreamTee

def sectionize(message):
    n = len(message)
    souligne = "\n" + n * "-" + "\n"
    return (souligne + message + souligne)

class PaquetExercice:
    def __init__(self, contenu: bytes, type_exo, métadonnées):
        self.contenu = contenu
        self.métadonnées = métadonnées
        if 'en_place' in self.métadonnées:
            del self.métadonnées['en_place']
        self.type_exo = type_exo

    def extrait(self, dest: str) -> 'Exerciseur':
        fichier_tar = tarfile.open(fileobj=io.BytesIO(self.contenu), mode='r:xz')
        fichier_tar.extractall(path=dest)
        rép_source = os.path.join(dest, 'src')
        return Exerciseur.avec_type(rép_source, en_place=True, type_exo = self.type_exo, **self.métadonnées)

    def __enter__(self):
        self.rép_extraction = tempfile.TemporaryDirectory()
        nom_rép_extraction = self.rép_extraction.__enter__()
        return self.extrait(nom_rép_extraction)

    def __exit__(self, *args):
        self.rép_extraction.__exit__(*args)

    def to_dict(self) -> Dict:
        return {
            'contenu': self.contenu,
            'métadonnées': self.métadonnées,
            'type_exo': self.type_exo
        }

    def vers_cbor(self) -> bytes:
        return cbor.dumps(self.to_dict())

    @classmethod
    def depuis_cbor(classe, x: bytes):
        return classe.from_dict(cbor.loads(x))


    @classmethod
    def from_dict(Classe, dico):
        return Classe(dico['contenu'], dico['type_exo'], dico['métadonnées'])

class Exerciseur(ABC):
    """
    Cette classe représente un exerciseur. Pour construire une image docker à partir
    d'un objet de cette classe, il faut disposer d'un répertoire de travail.

    On passe ensuite par trois étapes:
    - on copie les sources dans ce répertoire
    - `prépare_source` modifie les sources pour préparer la construction
    - `vers_exerciseur_dockerfile` crée un `ExerciseurDockerfile` pour pouvoir lancer la construction
      de l'image.
    """
    types_exerciseurs = {}

    @abstractmethod
    def __init__(self, sources: str, en_place: False, debug_out=None, **kwargs):
        self.sources = sources
        if en_place:
            self.rép_travail = sources
        else:
            self.rép_travail = None
        self.prêt = en_place
        self.debug_out = debug_out

    def debug(self, *args, **kwargs):
        if self.debug_out:
            print(*args, **kwargs, file=self.debug_out)

    @abstractmethod
    def copie_source(self) -> None:
        pass


    def métadonnées_src(self) -> Dict[str, str]:
        return self.métadonnées()

    @abstractmethod
    def métadonnées(self) -> Dict[str, str]:
        pass

    def prépare_métadonnées(self):
        self.meta = self.métadonnées()

    @abstractmethod
    def type_exo(self) -> str:
        pass

    def empaquète(self) -> PaquetExercice:
        def renomme(tar_info):
            p = tar_info.name
            
            # Vérification, est ce que self.sources est un répertoire
            if os.path.isdir(self.sources):
                if os.path.isabs(self.sources):
                    p = os.path.join('/', p)
                p = os.path.relpath(p, start=self.sources)
            else:
                # Si ce n'est pas un dossier, on garde juste le nom du fichier, pour éviter d'obtenir src/.
                p = os.path.basename(p)
            p = os.path.join('src', p)
            tar_info.name = p
            return tar_info
        contenu_tar = io.BytesIO()
        t = tarfile.open(fileobj=contenu_tar, mode='w:xz')
        t.add(self.sources, recursive=True, filter=renomme)
        t.close()
        return PaquetExercice(contenu_tar.getvalue(), self.type_exo(), self.métadonnées_src())

    @classmethod
    def avec_type(cls, répertoire: str, type_exo: str, *args, **kwargs) -> None:
        """
        Construit un exerciseur (de la sous-classe idoine).

        @param type_exo: le type d'exerciseur, parmi "DémonPython", "PackagePython", "TestsPython", "Dockerfile" ou "Jacadi", et pour la rétrocompatibilté, les types "python" (même fonctionnement que Jacadi) et "java" 
        @param répertoire: le dossier contenant les sources de l'exerciseur
        @param kwarg: un dictionnaire qui sert à donner des arguments supplémentaires en fonction de `type_exo`.
        - pour PackagePython, `nom_module="tralala"` indique quel module contient la classe exerciseur et `nom_classe="NomClasse"` le nom de cette classe
        - pour TestsPython, `nom_module="tralala"` indique quel module contient les tests
        - pour Jacadi et python (rétrocompatibilité), `module="mod_ens"` indique quel module contient le code enseignant. S'il n'est pas renseigné, il prendra le fichier python se trouvant dans le répertoire donné en paramètre (s'il n'y en a qu'un).
        - pour java (rétrocompatibilité), `nom_module="tralala"` indique quel module contient les tests et `classe_etu=Personnage` indique le nom de la classe que l'étudiant doit fournir. Si `classe_etu` n'est pas fourni, le nom de la classe attendu sera le nom de la classe du module de test sans le mot Test.

        @return l'objet exerciseur (de la sous-classe idoine d'Exerciseur).
        """
        Classe = cls.types_exerciseurs[type_exo]
        return Classe(répertoire, *args, **kwargs)


    @abstractmethod
    def utiliser_rép_travail(self, rép_travail: str) -> None:
        """
        Indique un répertoire à utiliser comme répertoire de travail pour la construction de l'image docker.
        """
        pass

    @abstractmethod
    def prépare_source(self) -> None:
        """
        Modifie les sources présentes dans rép_travail (si None, utilise le répertoire
        de travail obtenu avec `with self as t`)
        """
        pass

    @abstractmethod
    def écrit_dockerfile(self):
        """
        Finalise la création d'un ExerciseurDockerfile à partir du travail où les sources ont été
        copiées et préparées.
        """
        pass

    def crée_image(self, docker_client=None):
        """Crée l'image docker.

        Renvoie un couple (image, log). L'image est une chaîne de
        caractères contenant le hash de l'image qui a été construite;
        log est un itérateur des lignes du log de construction.
        """

        # registry_host = "pcap-registry:5000"
        # # registry_host = "127.0.0.1:5000"

        # if not self.rép_travail:
        #     raise ValueError("rép_travail doit être défini lors de l'appel à crée_image")
        # docker_client = docker_client or docker.from_env()

        # print("\n\nConstruction de l'image en cours...")
        # (image, log) = docker_client.images.build(path=self.rép_travail, quiet=True)
        # print(f"Image construite avec ID: {image.id}")  

        # nom_image=image.id.split(':')[1]
        # print(f"Tagging de l'image avec {registry_host}/exerciseur:{nom_image}")
        # image.tag(f'{registry_host}/exerciseur',nom_image)
        # try:
        #     print(f"Pushing de l'image {registry_host}/exerciseur:{nom_image} vers le registre...")
        #     push_response = docker_client.images.push(f'{registry_host}/exerciseur', tag=nom_image)
        #     print(f"Réponse push : {push_response}")
        # except Exception as e:
        #     print("Exception while pushing:", e)
        #     pass
        
        # if self.avec_openfaas:
        #     nom_fonction = nom_image[:62]

        #     gateway_url = "http://gateway:8080"
            
        #     # En local
        #     # gateway_url = "http://localhost:8080"

        #     headers = {"Content-Type": "application/json"}

        #     payload = {
        #         "service": nom_fonction,
        #         "image": f"{registry_host}/exerciseur:{nom_image}",
        #         "envProcess": "",
        #         "labels": {
        #             "com.openfaas.scale.min": "0"
        #         }
        #     }

        #     requests.post(f"{gateway_url}/system/functions", data=json.dumps(payload), headers=headers)



        # Version Kubernetes 

        import uuid
        import tarfile
        import base64
        import os
        import time
        from kubernetes import client, config

        creer_image_alpine()
        creer_image_alpine("openjdk")

        # 1. Infos image
        tag = str(uuid.uuid4())
        image_name = f"pcap-registry.pcap-api.svc.cluster.local:5000/exerciseur:{tag}"
        pod_name = f"kaniko-build-{tag}"

        # 2. Packager le contexte local (rép_travail) en tar.gz
        tar_path = f"/tmp/context-{tag}.tar.gz"
        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add(self.rép_travail, arcname=".")

        # 3. Lire et encoder le contenu
        with open(tar_path, "rb") as f:
            encoded_context = base64.b64encode(f.read()).decode()

        # 4. Charger config Kubernetes
        try:
            config.load_incluster_config()
        except:
            config.load_kube_config()

        api = client.CoreV1Api()

        # 5. Créer un Secret temporaire contenant le contexte encodé
        secret_name = f"kaniko-context-{tag}"
        secret = client.V1Secret(
            metadata=client.V1ObjectMeta(name=secret_name),
            type="Opaque",
            data={"context.tar.gz": encoded_context}
        )
        api.create_namespaced_secret(namespace="pcap-api", body=secret)

        # 6. Définir le Pod Kaniko avec initContainer qui extrait le contexte
        pod_spec = client.V1Pod(
            metadata=client.V1ObjectMeta(name=pod_name),
            spec=client.V1PodSpec(
                restart_policy="Never",
                containers=[
                    client.V1Container(
                        name="kaniko",
                        image="gcr.io/kaniko-project/executor:latest",
                        image_pull_policy="IfNotPresent",
                        args=[
                            "--dockerfile=/context/Dockerfile",
                            "--context=/context",
                            f"--destination={image_name}",
                            "--insecure",
                            "--skip-tls-verify"
                        ],
                        volume_mounts=[
                            client.V1VolumeMount(mount_path="/context", name="build-context")
                        ]
                    )
                ],
                init_containers=[
                    client.V1Container(
                        name="extract-context",
                        image="alpine",
                        image_pull_policy="IfNotPresent",
                        command=["sh", "-c", "mkdir -p /context && tar -xzf /secret/context.tar.gz -C /context"],
                        volume_mounts=[
                            client.V1VolumeMount(mount_path="/secret", name="context-archive"),
                            client.V1VolumeMount(mount_path="/context", name="build-context")
                        ]
                    )
                ],
                volumes=[
                    client.V1Volume(
                        name="context-archive",
                        secret=client.V1SecretVolumeSource(secret_name=secret_name)
                    ),
                    client.V1Volume(
                        name="build-context",
                        empty_dir={}
                    )
                ]
            )
        )

        # 7. Lancer le Pod
        api.create_namespaced_pod(namespace="pcap-api", body=pod_spec)
        print(f"Pod {pod_name} lancé, en attente de fin...")

        # 8. Attendre fin du build
        while True:
            pod = api.read_namespaced_pod(name=pod_name, namespace="pcap-api")
            if pod.status.phase in ["Succeeded", "Failed"]:
                break
            time.sleep(5)

        # logs = api.read_namespaced_pod_log(name=pod_name, namespace="pcap-api")
        logs = []
        # print("Logs Kaniko:\n", logs)

        # 9. Supprimer le secret temporaire
        api.delete_namespaced_secret(name=secret_name, namespace="pcap-api")

        # 10. Supprimer le Pod
        api.delete_namespaced_pod(name=pod_name, namespace="pcap-api", body=client.V1DeleteOptions())
        print(f"Pod {pod_name} supprimé.")

        # 11. Poster la fonction openfaas
        if self.avec_openfaas:
            from requests.auth import HTTPBasicAuth

            username = os.getenv("OPENFAAS_USERNAME")
            if not username:
                raise EnvironmentError("La variable OPENFAAS_USERNAME est manquante.")

            password = os.getenv("OPENFAAS_PASSWORD")
            if not password:
                raise EnvironmentError("La variable OPENFAAS_PASSWORD est manquante.")

            nom_fonction = tag[:62]
            gateway_url = "http://gateway:8080"
            headers = {"Content-Type": "application/json"}
            payload = {
                "service": nom_fonction,
                "image": image_name,
                "envProcess": "",
                "labels": {"com.openfaas.scale.min": "0"}
            }
            requests.post(f"{gateway_url}/system/functions", data=json.dumps(payload), headers=headers, auth=HTTPBasicAuth(username, password))

        return (image_name,logs)


    def construire(self) -> str:
        """
        Construit une image docker en utilisant comme répertoire de travail
        un répertoire temporaire.

        Renvoie une chaîne de caractères contenant le hash de l'image qui a été construite.
        """
        with tempfile.TemporaryDirectory() as rép_travail:
            self.utiliser_rép_travail(rép_travail + '/src')
            self.copie_source()
            self.prépare_source()
            self.écrit_dockerfile()
            i, log = self.crée_image()
            self.prépare_métadonnées()
            self.debug(sectionize("Logs construction image"))
            # for ligne in log:
            #     self.debug(ligne)
        # return i.id
        return i

    @classmethod
    def register(classe, nom, sous_classe):
        classe.types_exerciseurs[nom] = sous_classe

def liberer_openfaas(id_exo: str):
    import requests, json
    # r = requests.delete('http://gateway:8080/system/functions', data=json.dumps({ "functionName":id_exo}))
    r = requests.delete(f'http://gateway:8080/function/{id_exo}')

def creer_image_alpine(registre: str ="python"):
    """
    Créer et push dans le registry privé (pcap-registry) dans le repository "utils"
    une image alpine en fonction du registre donné en paramètre.
    Passe par un pod Kaniko qui fait la création de l'image et la push dans le registry privé.

    @param registre: le registre utilisé pour pull l'image parmi python et openjdk, défaut à python

    """
    from kubernetes import client, config
    import time

    registry_host = "pcap-registry.pcap-api.svc.cluster.local:5000"
    repository = "utils"

    try:
        config.load_incluster_config()
    except:
        config.load_kube_config()
    api = client.CoreV1Api()

    if registre=="openjdk":
        pod_name = "kaniko-push-openjdk-alpine"
        destination = "openjdk:alpine"
    else: # Python
        pod_name = "kaniko-push-python-alpine"
        destination = "python:alpine3.8"

    full_image_name = f"{registry_host}/{repository}:{destination}"

    if image_exists(registry_host, repository, destination):
        print(f"Image {full_image_name} déjà présente dans le registry, pas de build nécessaire.")
        return

    namespace = "pcap-api"

    print(sectionize(f"CREATION ET PUBLICATION DANS LE REGISTRY (pcap-registry) : {destination}"))

    pod_manifest = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "name": pod_name,
        },
        "spec": {
            "restartPolicy": "Never",
            "containers": [
                {
                    "name": "kaniko",
                    "image": "gcr.io/kaniko-project/executor:latest",
                    "args": [
                        "--dockerfile=/workspace/Dockerfile",
                        "--context=dir:///workspace/",
                        f"--destination={full_image_name}",
                        "--insecure",
                        "--skip-tls-verify",
                    ],
                    "volumeMounts": [
                        {
                            "name": "workspace",
                            "mountPath": "/workspace"
                        }
                    ]
                }
            ],
            "volumes": [
                {
                    "name": "workspace",
                    "configMap": {
                        "name": "kaniko-dockerfile-configmap"
                    }
                }
            ]
        }
    }

    config_map = client.V1ConfigMap(
        metadata=client.V1ObjectMeta(name=f"kaniko-dockerfile-configmap-{destination}"),
        data={f"Dockerfile": "FROM {destination}\n"}
    )

    try:
        api.create_namespaced_config_map(namespace=namespace, body=config_map)
    except client.exceptions.ApiException as e:
        if e.status == 409:
            print("ConfigMap déjà existant, on continue...")
        else:
            raise

    try:
        api.create_namespaced_pod(namespace=namespace, body=pod_manifest)
        print("Pod Kaniko créé, attente de fin...")
    except client.exceptions.ApiException as e:
        if e.status == 409:
            print("Pod déjà existant, suppression en cours...")
            api.delete_namespaced_pod(name=pod_name, namespace=namespace)
            time.sleep(5)
            api.create_namespaced_pod(namespace=namespace, body=pod_manifest)
        else:
            raise

    while True:
        pod_status = api.read_namespaced_pod_status(name=pod_name, namespace=namespace)
        phase = pod_status.status.phase
        if phase in ["Succeeded", "Failed"]:
            print(f"Pod terminé avec le statut : {phase}")
            break
        print(f"Pod en cours... statut : {phase}")
        time.sleep(5)

    logs = api.read_namespaced_pod_log(name=pod_name, namespace=namespace)
    print("--- Logs Kaniko ---")
    print(logs)

    api.delete_namespaced_pod(name=pod_name, namespace=namespace)
    api.delete_namespaced_config_map(name="kaniko-dockerfile-configmap", namespace=namespace)
    print("Nettoyage effectué.")

    print(sectionize(f"FIN CREATION ET PUBLICATION DANS LE REGISTRY (pcap-registry) : {destination}"))

def image_exists(registry_url, repository, tag):
    url = f"http://{registry_url}/v2/{repository}/manifests/{tag}"
    headers = {"Accept": "application/vnd.docker.distribution.manifest.v2+json"}
    try:
        response = requests.head(url, headers=headers, timeout=5, verify=False)  # verify=False si TLS auto-signé
        return response.status_code == 200
    except requests.RequestException:
        return False

if __name__ == "__main__":
    creer_image_alpine()
    creer_image_alpine("openjdk")