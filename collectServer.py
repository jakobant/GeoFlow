
import socket
from utils import MaxmindDB

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('localhost', 9991)
sock.bind(server_address)
readmax = MaxmindDB({'maxminddb_path': './db/GeoLite2-City.mmdb'})

c = 0
count = {}
while True:
    data, address = sock.recvfrom(4096)
    ip, status, method, path = data.decode().split(',')
    geo_data = readmax.get_geodata(ip)
    try:
        count['{}|{}|{}'.format(ip, status, method)] += 1
    except KeyError:
        count['{}|{}|{}'.format(ip, status, method)] = 1

    c += 1
    if c == 10:
        for key in count:
            iip, sstatus, mmethod = key.split('|')
            rdata = {
                'ip': iip,
                'status': sstatus,
                'method': mmethod,
                'path': '',
                'count': count[key],
                'geo': geo_data
            }
            print(rdata)
        c = 0
        count = {}
        print("-------------------------------")



