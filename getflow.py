import socket, struct

from socket import inet_ntoa
import maxminddb
import redis
import json
from const import META, PORTMAP
import syslog
from time import sleep


SIZE_OF_HEADER = 24
SIZE_OF_RECORD = 48

HOMEIP = '85.220.92.23'
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', 9998))
readmax = maxminddb.open_database('./db/GeoLite2-City.mmdb')
r = redis.StrictRedis(host='127.0.0.1', port=6379, db=0)

def clean_db(unclean):
    selected = {}
    for tag in META:
        head = None
        try:
            if tag['tag'] in unclean:
                head = unclean[tag['tag']]
                for node in tag['path']:
                    if node in head:
                        head = head[node]
                    else:
                        head = None
                        break
                selected[tag['lookup']] = head
        except:
            None

    return selected

def merge_dicts(*args):
    super_dict = {}
    for arg in args:
        super_dict.update(arg)
    return super_dict

def find_hq_lat_long(hq_ip):
    hq_ip_db_unclean = readmax.get(hq_ip)
    if hq_ip_db_unclean:
        hq_ip_db_clean = clean_db(hq_ip_db_unclean)
        dst_lat = hq_ip_db_clean['latitude']
        dst_long = hq_ip_db_clean['longitude']
        hq_dict = {
                'dst_lat': dst_lat,
                'dst_long': dst_long
                }
        return hq_dict
    else:
        print('Please provide a valid IP address for headquarters')

hq_ip = find_hq_lat_long(HOMEIP)

while True:
    buf, addr = sock.recvfrom(8192)

    (version, count) = struct.unpack('!HH', buf[0:4])
    if version != 5:
        print("Not NetFlow v5!")
        continue

    # It's pretty unlikely you'll ever see more then 1000 records in a 1500 byte UDP packet
    if count <= 0 or count >= 8192:
        print("Invalid count %s" % count)
        continue

    ps = {}
    pc = {}
    for i in range(0, count):
        try:
            base = SIZE_OF_HEADER + (i * SIZE_OF_RECORD)

            data = struct.unpack('!IIIIHH', buf[base + 16:base + 36])

            nfdata = {}
            nfdata['saddr'] = inet_ntoa(buf[base + 0:base + 4])
            nfdata['daddr'] = inet_ntoa(buf[base + 4:base + 8])
            nfdata['pcount'] = data[0]
            nfdata['bcount'] = data[1]
            nfdata['stime'] = data[2]
            nfdata['etime'] = data[3]
            nfdata['sport'] = data[4]
            nfdata['dport'] = data[5]
            nfdata['protocol'] = buf[base + 38]
        except:
            print("err")
            continue
        if (nfdata['saddr']) == '192.168.2.1':
            try:
                ps['{}-{}-{}'.format(nfdata['daddr'], nfdata['dport'], nfdata['protocol'])] += nfdata['bcount']
            except:
                ps['{}-{}-{}'.format(nfdata['daddr'], nfdata['dport'], nfdata['protocol'])] = nfdata['bcount']
            try:
                pc['{}-{}-{}'.format(nfdata['daddr'], nfdata['dport'], nfdata['protocol'])] += nfdata['pcount']
            except:
                pc['{}-{}-{}'.format(nfdata['daddr'], nfdata['dport'], nfdata['protocol'])] = nfdata['pcount']

    #print(pc)
    #print(ps)
    cc = 1
    for key in ps:
        ip, port, protocol = key.split('-')
        mx = clean_db(readmax.get(ip))
        #print(clean_db(readmax.get(ip)))
        js = {
            'src_ip': ip,
            'dst_ip': HOMEIP,
            'src_port': port,
            'protocol': protocol,
            'pcount': pc[key],
            'bcount': ps[key]
        }
        msg = '{},{},{},{},{},{}'.format(ip, HOMEIP, port, port, port, pc[key])
        syslog.syslog(msg)
        jd = merge_dicts(js, mx, hq_ip)
        json_data = json.dumps(jd)
        cc += 1
        sleep(0.1)
        if cc > 34:
            break
        #r.publish('attack-map-production', json_data)

