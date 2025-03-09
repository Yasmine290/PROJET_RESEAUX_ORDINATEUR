''' dans ce code, le serveur foonctionne de cette manière:
d'abord, il charge les ressources à partir d'un fichier JSON appelé ressources.json.
Ensuite, il écoute les connexions entrantes sur l'adresse IP et le port spécifiés.
Lorsqu'un client se connecte, un nouveau thread est créé pour gérer la connexion.
Le serveur traite les requêtes GET et POST des clients en fonction de l'opération spécifiée dans la requête.
Pour les requêtes GET, le serveur renvoie les données de la ressource demandée si elle existe, sinon il renvoie un code d'erreur 404.
Pour les requêtes POST, le serveur crée ou met à jour la ressource spécifiée avec les données fournies par le client.
Le serveur envoie ensuite une réponse au client avec un code de statut approprié.
Le serveur peut également notifier les clients abonnés lorsqu'une ressource est créée ou mise à jour en envoyant les nouvelles données aux clients abonnés.
Enfin, le serveur enregistre les ressources mises à jour dans le fichier ressources.json pour les conserver entre les redémarrages du serveur.
Le serveur utilise un journal pour enregistrer les événements importants, tels que les erreurs lors du traitement des requêtes.
Le serveur peut être démarré en exécutant la fonction demarrer_serveur() dans le script serveur.py.
Le serveur peut être arrêté en appuyant sur Ctrl + C dans la console où il est en cours d'exécution.

'''




import socket
import json
import threading
import logging
from collections import defaultdict

# Configuration du journal

'''
Le module logging est utilisé pour enregistrer les événements importants, tels que les erreurs, les avertissements et les informations, dans un fichier journal.
Le fichier journal est configuré pour enregistrer les messages avec un horodatage, un niveau de gravité et un message.
Les messages sont enregistrés dans le fichier server.log situé dans le même répertoire que le script serveur.py.
Le niveau de gravité est défini sur INFO, ce qui signifie que seuls les messages d'information et de gravité supérieure seront enregistrés.
cela a pour avantages de:
- Faciliter le débogage en enregistrant les événements importants dans un fichier journal.
- Permettre de suivre l'historique des événements survenus sur le serveur.
- Aider à identifier les problèmes potentiels et à les résoudre plus rapidement.
- Améliorer la fiabilité et la stabilité du serveur en enregistrant les erreurs et les avertissements.
- Fournir des informations utiles sur le fonctionnement du serveur et les interactions avec les clients.
'''
logging.basicConfig(filename='server.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

authorized_users = {
    "user1": "password1",
    "user2": "password2"
}


ressources = {}  # Dictionnaire pour stocker les ressources

# Dictionnaire pour stocker les clients abonnés à chaque ressource, avec la clé étant l'ID de la ressource et la valeur étant un ensemble de clients
#cela permet de garder une trace des clients qui sont abonnés à une ressource spécifique, afin de pouvoir les notifier lorsque la ressource est mise à jour.
#Cela est utile pour les clients qui souhaitent recevoir des mises à jour en temps réel sur une ressource particulière.
client_subscriptions = defaultdict(set)

# Fonctions pour charger et sauvegarder les ressources à partir d'un fichier JSON:
#cette fonctionne de cette manière:
#- La fonction charger_ressources(fichier_ressources='ressources.json') charge les ressources à partir d'un fichier JSON spécifié (par défaut ressources.json).
#- La fonction sauvegarder_ressources(ressources, fichier_ressources='ressources.json') enregistre les ressources dans un fichier JSON spécifié (par défaut ressources.json).
#- Les ressources sont stockées dans un dictionnaire où la clé est l'ID de la ressource et la valeur est le contenu de la ressource.
#- Les ressources sont enregistrées dans un fichier JSON avec une indentation de 2 espaces pour une meilleure lisibilité.

def charger_ressources(fichier_ressources='ressources.json'):
    try:
        with open(fichier_ressources, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def sauvegarder_ressources(ressources, fichier_ressources='ressources.json'):
    with open(fichier_ressources, 'w') as f:
        json.dump(ressources, f, indent=2)


'''
ici, la fonction notifier_clients(rsrcId, data) est utilisée pour notifier les clients abonnés à une ressource spécifique lorsqu'elle est mise à jour.
La fonction prend l'ID de la ressource et les nouvelles données de la ressource comme arguments.
Elle crée un message de notification contenant l'adresse IP du serveur, le code de statut 210 (mise à jour de la ressource), l'ID de la ressource et les nouvelles données.
Elle envoie ensuite le message de notification à chaque client abonné à la ressource en utilisant la méthode send() du socket du client.
Si une erreur se produit lors de l'envoi de la notification à un client, elle est capturée et enregistrée dans le journal.
La fonction notifier_clients() est appelée après la mise à jour d'une ressource pour informer les clients abonnés des modifications apportées à la ressource.
Cela permet aux clients de recevoir des mises à jour en temps réel sur les ressources auxquelles ils sont abonnés.

'''
pending_notifications = defaultdict(list)

def notifier_clients(rsrcId, data):
   if rsrcId in client_subscriptions:
        notification = json.dumps({
            "server": socket.gethostbyname(socket.gethostname()),
            "code": "210",
            "rsrcId": rsrcId,
            "data": data,
            "message": ""
        })
        for client in client_subscriptions[rsrcId]:
            try:
                client.send(notification.encode())
            except Exception as e:
                logging.error(f"Erreur lors de la notification du client : {e}")
                # En cas d'erreur, stockez la notification en attente pour ce client
                pending_notifications[client].append(notification)

'''
La fonction traiter_requete(client, adresse_ip, port) est utilisée pour traiter les requêtes des clients.
Elle fonctionne en boucle pour recevoir les données du client, les analyser en tant qu'objets JSON et traiter les opérations GET et POST.
Pour les requêtes GET, elle vérifie si la ressource demandée existe dans le dictionnaire des ressources.
Si la ressource existe, elle renvoie les données de la ressource avec un code de statut 200 (OK) ou 210 (mise à jour de la ressource) si le protocole est "rdo".
Si la ressource n'existe pas, elle renvoie un code de statut 404 (non trouvé) avec un message d'erreur.
Pour les requêtes POST, elle crée ou met à jour la ressource spécifiée avec les données fournies par le client.
Elle envoie ensuite une réponse au client avec un code de statut approprié (201 pour une nouvelle ressource, 211 pour une ressource mise à jour).
Elle ajoute également le client à l'ensemble des clients abonnés à la ressource pour les futures notifications.
La fonction traiter_requete() est appelée dans un thread séparé pour chaque client connecté au serveur.
Cela permet au serveur de gérer plusieurs clients simultanément et de traiter leurs requêtes de manière asynchrone.

'''               

def traiter_requete(client, adresse_ip, port):
    while True:
        data = client.recv(4096)
        if not data:
            break
        requete = json.loads(data.decode('utf-8'))
        operation = requete.get("operation")
        rsrcId = requete.get("rsrcId")
        contenu = requete.get("data", None)
        
        if operation == "GET":
            if rsrcId in ressources:
                code = "200" if requete["protocol"] == "wrdo" else "210"
                client_subscriptions[rsrcId].add(client)
                logging.info(f"Taitement GET ID ressource {client}")
                reponse = json.dumps({"server": adresse_ip, "code": code, "rsrcId": rsrcId, "data": ressources[rsrcId], "message": ""})
                
            else:
                reponse = json.dumps({"server": adresse_ip, "code": "404", "rsrcId": rsrcId, "data": "", "message": "ressource inconnue"})
            client.sendall(reponse.encode('utf-8'))
        elif operation == "POST":
            isNew = rsrcId not in ressources
            if "login" in requete and "password" in requete:
                login = requete["login"]
                password = requete["password"]
                if login in authorized_users and authorized_users[login] == password:
                    # Authentification réussie
                    logging.info(f"Authentification réussie pour {login}")
                else:
                    # Authentification échouée
                    logging.warning(f"Tentative de connexion infructueuse pour {login}")
                    client.sendall(json.dumps({"message": "Authentification échouée"}).encode())
                    return
            else:
                # Authentification requise mais informations manquantes
                logging.warning("Authentification requise mais informations manquantes")
                client.sendall(json.dumps({"message": "Authentification requise"}).encode())
                return
            ressources[rsrcId] = contenu
            sauvegarder_ressources(ressources)
            code = "201" if isNew else "211"
            logging.info(f"Taitement POST ID ressource {rsrcId}")
            message = "Ressource créée" if isNew else "Ressource mise à jour"
            notifier_clients(rsrcId, contenu)  # Notifie les clients abonnés à cette ressource
            reponse = json.dumps({"server": adresse_ip, "code": code, "rsrcId": rsrcId, "message": message})
            client.sendall(reponse.encode('utf-8'))

    client.close()
'''
La fonction client_handler(client, adresse_ip, port) est utilisée pour gérer les connexions entrantes des clients.
Elle appelle la fonction traiter_requete(client, adresse_ip, port) pour traiter les requêtes du client.
Elle capture les exceptions qui se produisent lors du traitement des requêtes et les enregistre dans le journal.
Elle ferme ensuite la connexion avec le client une fois le traitement de la requête terminé.
La fonction client_handler() est appelée dans un thread séparé pour chaque client connecté au serveur.
son but est de traiter les requêtes des clients et de gérer les connexions avec eux de manière asynchrone.
cela garatit  que le serveur peut gérer plusieurs clients simultanément et traiter leurs requêtes de manière indépendante.

'''
def client_handler(client, adresse_ip, port):
    try:
        
        if client in pending_notifications:
            for notification in pending_notifications[client]:
                client.send(notification.encode())
                logging.error(f"notification ennvouyer")
            # Effacer les notifications en attente une fois envoyées
            del pending_notifications[client]
            
        traiter_requete(client, adresse_ip, port)
        
    except Exception as e:
        logging.error(f"Erreur lors du traitement de la requête: {e}")
    finally:
        client.close()

'''
enfin cette fonction demarrer_serveur(adresse=' assure que le serveur démarre sur l'adresse IP spécifiée (par défaut
en utilisant le socket.gethostbyname(socket.gethostname()) pour obtenir l'adresse IP de la machine locale) et le port spécifié (par défaut 80).
Elle charge les ressources à partir du fichier ressources.json en utilisant la fonction charger_ressources().
Elle crée un socket serveur en utilisant socket.socket() avec les paramètres socket.AF_INET et socket.SOCK_STREAM.
Elle lie le socket serveur à l'adresse et au port spécifiés en utilisant la méthode bind().
Elle écoute les connexions entrantes en utilisant la méthode listen().
Elle accepte les connexions entrantes des clients en utilisant la méthode accept() du socket serveur.
Elle crée un nouveau thread pour chaque client connecté en appelant la fonction client_handler(client, adresse_ip, port).
Elle démarre le thread du client en appelant la méthode start() du thread.
La fonction demarrer_serveur() est la fonction principale qui démarre le serveur et gère les connexions entrantes des clients.
Elle permet au serveur de fonctionner en continu, d'accepter les connexions des clients et de traiter leurs requêtes de manière asynchrone.

'''

def demarrer_serveur(adresse='0.0.0.0', port=80):
    global ressources
    adresse_ip = socket.gethostbyname(socket.gethostname())
    ressources = charger_ressources()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serveur:
        serveur.bind((adresse, port))
        serveur.listen()
        print(f"Serveur démarré à {adresse_ip}:{port}. En attente de connexions...")
        logging.info(f"Serveur démarré à {adresse_ip}:{port}. En attente de connexions...")
        while True:
            client, addr = serveur.accept()
            logging.info(f"le client {addr}connecte serveur")
            print(f"le client {addr}connecte serveur")
            client_thread = threading.Thread(target=client_handler, args=(client, adresse_ip, port))
            client_thread.start()

if __name__ == "__main__":
    # Vous pouvez modifier ici pour spécifier une adresse et un port différent
    demarrer_serveur()
