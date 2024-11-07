import json
import socket
import threading
import time
import sys

PORT = 19000
MY_IP = ''
NEIGHBOR_IPS = []

args = sys.argv[1:]
if len(args) == 0:
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
        MY_IP = config['myIp']
        NEIGHBOR_IPS = config['ips']
else:
    MY_IP = args[0]
    NEIGHBOR_IPS = args[1:]

print(f"IP: {MY_IP}")
print(f"Vizinhos: {NEIGHBOR_IPS}")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((MY_IP, PORT))
table = {}
neighbors_update_time = {}

for ip in NEIGHBOR_IPS:
    table[ip] = {'ip': ip, 'metric': 1, 'exit': ip}


def send_table():
    global sock
    while True:
        msg = ""
        for entry in table.values():
            msg += f"!{entry['ip']}:{entry['metric']}"
        if (len(msg) == 0):
            continue
        for ip in NEIGHBOR_IPS:
            try:
                sock.sendto(msg.encode(), (ip, PORT))
            except:
                sock.close()
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.bind((MY_IP, PORT))
                sock.sendto(msg.encode(), (ip, PORT))

        print("\033[92m" + f"SENDING: {msg}")
        time.sleep(15)


def table_entry_killer():
    time.sleep(35)
    while True:
        for ip in list(NEIGHBOR_IPS):
            if (ip not in neighbors_update_time) or (time.time() - neighbors_update_time[ip] > 35):
                NEIGHBOR_IPS.remove(ip)
                ips_to_remove = [el for el in table if table[el]['exit'] == ip]
                for ip_to_remove in ips_to_remove:
                    table.pop(ip_to_remove)
                    print(
                        "\033[91m" + f"REMOVING {ip_to_remove} FROM TABLE BECAUSE {ip} IS DEAD")
        time.sleep(35)


def received_from_ip(ip):
    neighbors_update_time[ip] = time.time()


def receive_thread():
    global sock
    while True:
        try:
            text, addr = sock.recvfrom(1024)
            addr = addr[0]
            text = text.decode()
            print("\033[94m" + f"RECEIVING: {text} \t FROM: {addr}")
            received_from_ip(addr)
            if text[0] == b'':
                continue
            elif text[0] == '!':
                ips = [el for el in text.split('!') if el != '']
                for ip in ips:
                    ip, metric = ip.split(':')
                    if ip == MY_IP:
                        continue
                    if ip not in table:
                        table[ip] = {'ip': ip, 'metric': int(
                            metric) + 1, 'exit': addr}
                        continue
                    if (table[ip]['metric'] > int(metric) + 1) or (table[ip]['exit'] == addr):
                        table[ip]['metric'] = int(metric) + 1
                        table[ip]['exit'] = addr

                for obj in list(table.values()):
                    ips_list = [ip.split(':')[0] for ip in ips]

                    if (obj['exit'] == addr) and (obj['ip'] not in ips_list) and (obj['ip'] != obj['exit']):
                        table.pop(obj['ip'])
                        print("\033[91m" + f"REMOVING {obj['ip']} FROM TABLE")

            elif text[0] == '@':
                table[addr] = {'ip': addr, 'metric': 1, 'exit': addr}
                if (addr not in NEIGHBOR_IPS):
                    NEIGHBOR_IPS.append(addr)
                continue
            elif text[0] == '&':
                continue

        except ConnectionResetError:
            sock.close()
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind((MY_IP, PORT))


def enter_message():
    msg = f"@{MY_IP}:"
    for ip in NEIGHBOR_IPS:
        sock.sendto(msg.encode(), (ip, PORT))


enter_message()

send_thread = threading.Thread(target=send_table)
receive_thread = threading.Thread(target=receive_thread)
killer = threading.Thread(target=table_entry_killer)

send_thread.start()
receive_thread.start()
killer.start()
