import socket
import json
import getpass
def authenticate_user():
    # Demander à l'utilisateur de saisir ses informations d'identification
    username = input("Nom d'utilisateur : ")
    password = getpass.getpass("Mot de passe : ")
    return username, password


def handle_notification(notification):
    rsrc_id = notification["rsrcId"]
    new_data = notification["data"]
    print(f"Notification reçue pour la ressource {rsrc_id}:")
    print(json.dumps(notification, indent=2))
    print(f"Nouvelles données: {new_data}")



def send_request(host, port, request):
    host=socket.gethostbyname(socket.gethostname())
    port=80
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(json.dumps(request).encode())
        try:
            response = json.loads(s.recv(1024).decode())
            if "code" in response and response["code"] == "210":
                handle_notification(response)
            else:
                return response
        except Exception as e:
            print(f"Erreur lors de la réception de la réponse : {e}")
            return None




def handle_command(command):
    parts = command.split()
    if parts[0] == "GET":
        protocol, host_port_rsrc_id = parts[1].split("://")
        host, port_rsrc_id = host_port_rsrc_id.split(":")
        port = int(port_rsrc_id.split("/")[0])
        rsrc_id = "/".join(port_rsrc_id.split("/")[1:])
        request = {"protocol": protocol, "operation": "GET", "rsrcId": rsrc_id}
        response = send_request(host, port, request)
        print(json.dumps(response, indent=2))
        if "notifications" in response:
            print("Notifications :")
            for notification in response["notifications"]:
                print(notification)
    elif parts[0] == "POST":
        try:
            protocol, host_port_rsrc_id = parts[1].split("://")
            host, port_rsrc_id = host_port_rsrc_id.split(":")
            port = int(port_rsrc_id.split("/")[0])
            rsrc_id = "/".join(port_rsrc_id.split("/")[1:])
            
            data = json.loads(" ".join(parts[2:]))
            username, password = authenticate_user()
                
            #print({data})
            #formatted_data = format_student_data(data)
            #print("contenu", data)
            #print("contenu", formatted_data)
            request = {"protocol": protocol, "operation": "POST", "data": data, "rsrcId": rsrc_id, "login": username, "password": password}
            #print({rsrc_id})
            response = send_request(host, port, request)
            print(json.dumps(response, indent=2))
        except (ValueError, IndexError) as e:
            print(f"Erreur dans le format de la commande POST : {e}")
    else:
        print("Commande invalide")

while True:
    command = input(">")
    handle_command(command)
