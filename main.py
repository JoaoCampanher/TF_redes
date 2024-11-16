import json
import socket
import threading
import time
import sys

PORT = 19000
MY_IP = ''
NEIGHBOR_IPS = []


def get_my_ip():
    hostname = socket.gethostname()
    my_ip = socket.gethostbyname(hostname)
    return my_ip


def get_ips_from_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    ips = [line.split('#')[0].strip()
           for line in lines if line.strip() and not line.startswith('#')]
    return ips

# pode receber argumentos de três formas
# 1 - Arquivo roteadores.txt, onde cada linha é um ip de um roteador vizinho, e o próprio ip é obtido automaticamente
# 2 - Argumentos na linha de comando:
#   2.1 - Para obter próprio ip automaticamente: "python main.py - <ip_vizinho1> <ip_vizinho2> ..."
#   2.2 - Para inserir próprio ip manualmente: "python main.py <meu_ip> <ip_vizinho1> <ip_vizinho2> ..."

args = sys.argv[1:]
if len(args) == 0:
    MY_IP = get_my_ip()
    all_ips = get_ips_from_file('roteadores.txt')
    NEIGHBOR_IPS = [ip for ip in all_ips if ip != MY_IP]
else:
    MY_IP = args[0]
    if MY_IP == '-':
        MY_IP = get_my_ip()
    NEIGHBOR_IPS = args[1:]

print(f"IP: {MY_IP}")
print(f"Vizinhos: {NEIGHBOR_IPS}")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((MY_IP, PORT))
# Tabela de roteamento utilizada
table = {}
# Dicionário que armazena o tempo da última atualização de cada vizinho
neighbors_update_time = {}


def print_table():
    if len(table) == 0:
        print("\033[93m" + "EMPTY TABLE")
        return

    print('\033[93m' + '\nDESTINO \t MÉTRICA \t SAÍDA')
    for entry in table.values():
        print(
            "\033[93m" + f"{entry['ip']} \t {entry['metric']} \t\t {entry['exit']}")
    print()


# Inicia tabela com os vizinhos
for ip in NEIGHBOR_IPS:
    table[ip] = {'ip': ip, 'metric': 1, 'exit': ip}
# Função que envia a tabela para os vizinhos a cada 15 segundos


def send_table():
    global sock
    time.sleep(15)
    while True:
        msg = ""

        print_table()
        time.sleep(15)
        # Caso a tabela esteja vazia, não envia nada
        if len(table) == 0:
            continue

        for entry in table.values():
            # Constrói a mensagem com a tabela no formato
            msg += f"!{entry['ip']}:{entry['metric']}"

        # Envia a mensagem para todos os vizinhos
        for ip in NEIGHBOR_IPS:
            try:
                sock.sendto(msg.encode(), (ip, PORT))
            except:
                sock.close()
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.bind((MY_IP, PORT))
                sock.sendto(msg.encode(), (ip, PORT))

        # \033[92m determina a cor do texto no terminal
        print("\033[92m" + f"SENDING: {msg}")

# Função que remove entradas da tabela que não foram atualizadas por 35 segundos


def table_entry_killer():
    time.sleep(35)
    while True:
        # Para todos vizinhos
        for ip in list(NEIGHBOR_IPS):
            # Se o vizinho não enviou mensagem por 35 segundos
            if (ip not in neighbors_update_time) or (time.time() - neighbors_update_time[ip] > 35):
                # Remove o vizinho da lista de vizinhos
                NEIGHBOR_IPS.remove(ip)
                # Entradas da tabela que possuem o vizinho como saída
                ips_to_remove = [el for el in table if table[el]['exit'] == ip]
                # Remove todas estas entradas da tabela, pois uma mensagem para aquele destino teria que passar por um vizinho morto
                for ip_to_remove in ips_to_remove:
                    table.pop(ip_to_remove)
                    print(
                        "\033[91m" + f"REMOVING {ip_to_remove} FROM TABLE BECAUSE {ip} IS DEAD")
        time.sleep(35)

# Função que atualiza o tempo da última atualização de um vizinho
# É chamada toda vez que uma mensagem é recebida de um vizinho


def received_from_ip(ip):
    neighbors_update_time[ip] = time.time()

# Função que recebe mensagens de vizinhos


def receive():
    global sock
    while True:
        try:
            text, addr = sock.recvfrom(1024)
            addr = addr[0]
            text = text.decode()
            print("\033[94m" + f"RECEIVING: {text} \t FROM: {addr}")
            # Atualiza o tempo da última atualização do vizinho
            received_from_ip(addr)

            # Caso a mensagem seja de atualização de vizinhos
            if text[0] == '!':
                # Separa a mensagem em pares ip:metric
                ips = [el for el in text.split('!') if el != '']

                for ip in ips:
                    # Separa o ip e a métrica
                    ip, metric = ip.split(':')
                    # Ignora o próprio ip
                    if ip == MY_IP:
                        continue
                    # Se o ip não está na tabela, adiciona com métrica + 1
                    if ip not in table:
                        table[ip] = {'ip': ip, 'metric': int(
                            metric) + 1, 'exit': addr}
                        continue
                    # Se a métrica do ip na tabela é maior que a métrica recebida + 1 substitui
                    # OU
                    # Se a saída do ip na tabela é o ip que enviou a mensagem, então o caminho antigo não é mais válido. Logo, atualiza a tabela
                    if (table[ip]['metric'] > int(metric) + 1) or (table[ip]['exit'] == addr):
                        table[ip]['metric'] = int(metric) + 1
                        table[ip]['exit'] = addr
                # Para TODAS as entradas na tabela
                for obj in list(table.values()):
                    # Obtem os ips, sem as portas
                    ips_list = [ip.split(':')[0] for ip in ips]

                    # SENDER = ip que enviou a mensagem
                    #
                    # Se a saída de um ip na tabela é o SENDER
                    # E
                    # O SENDER não referencia mais este ip na própria tabela
                    # Então devemos remover este ip da tabela
                    #
                    # (obj['ip'] != obj['exit']) é uma verificação para não remover o ips que tem a si mesmo
                    # como saída, para impedir que entradas válidas de vizinhos sejam removidas
                    if (obj['exit'] == addr) and (obj['ip'] not in ips_list) and (obj['ip'] != obj['exit']):
                        # Remove o ip da tabela
                        table.pop(obj['ip'])
                        print("\033[91m" + f"REMOVING {obj['ip']} FROM TABLE")

            # Caso a mensagem seja de um novo vizinho que está se conectando agora
            elif text[0] == '@':
                # Insire o ip na tabela com métrica 1 e saída para ele mesmo
                table[addr] = {'ip': addr, 'metric': 1, 'exit': addr}
                # Adiciona o ip na lista de vizinhos, caso não esteja lá
                if (addr not in NEIGHBOR_IPS):
                    NEIGHBOR_IPS.append(addr)
            elif text[0] == '&':
                # Separa a mensagem em partes
                origin = text.split('%')[0][1:]
                destination = text.split('%')[1]
                message = text.split('%')[2]
                # Se o destino é o próprio ip, imprime a mensagem
                if destination == MY_IP:
                    print("\033[97m" +
                          f"Mensagem recebida de {origin}: {message}")
                    continue
                # Se o destino não está na tabela, imprime erro
                if destination not in table:
                    print("\033[91m" +
                          "IP de destino não encontrado na tabela")
                    continue
                # Se o destino está na tabela, envia a mensagem para o próximo salto
                print(
                    "\033[97m" + f"Encaminhando mensagem \"{message}\" de {origin} para {destination}")
                exit_ip = table[destination]['exit']
                sock.sendto(text.encode(), (exit_ip, PORT))

            else:
                print("\033[91m" +
                      f"Texto inválido recebido \"{text}\" de {addr}")

        except ConnectionResetError:
            sock.close()
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind((MY_IP, PORT))


def message_sender():
    while True:
        message = input("\033[97m" + "Insira a mensagem: \n")
        destination = input("\033[97m" + "Insira o ip de destino: \n")
        if destination not in table:
            print("\033[91m" + "IP de destino não encontrado na tabela")
            continue
        exit_ip = table[destination]['exit']
        sock.sendto(
            f"&{MY_IP}%{destination}%{message}".encode(), (exit_ip, PORT))

# Função que envia uma mensagem para todos os vizinhos, quando entra na rede


def enter_message():
    msg = f"@{MY_IP}"
    for ip in NEIGHBOR_IPS:
        sock.sendto(msg.encode(), (ip, PORT))


# Envia mensagem para todos os vizinhos, informando que entrou na rede
enter_message()

# Cria e inicia as threads, contendo:
# - Função de envio da tabela de roteamento
# - Função de recebimento de mensagens
# - Função de remoção de entradas da tabela
send_thread = threading.Thread(target=send_table)
receive_thread = threading.Thread(target=receive)
killer = threading.Thread(target=table_entry_killer)
messenger = threading.Thread(target=message_sender)
send_thread.start()
receive_thread.start()
killer.start()
messenger.start()
