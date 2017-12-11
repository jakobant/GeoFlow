import yaml
import re
from pygtail import Pygtail
import socket
import maxminddb
import logging

class YamlConfig:

    """Config Wrapper"""

    def __init__(self, configfile):
        self.cfg = self.load_config(configfile)

    def get_config(self):
        return self.cfg

    def load_config(self, file):
        with open(file, 'r') as ymlfile:
            cfg = yaml.load(ymlfile)
        return cfg


class UDPClient:

    """Main udp send message"""

    def __init__(self, config):
        self.server = config['udp_server']
        self.port = config['udp_port']
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(1)
        self.server_address = (self.server, int(self.port))
        self.exclude_status = config['exclude_status'].split(",")

    def send_message(self, message):
        self.sock.sendto(message.encode(), self.server_address)

class HttpAgent:

    """Main http file agent collector"""

    def __init__(self, config):
        self.file = config['file']
        self.exclude_status = config['exclude_status']
        self.file_type = config['file_type']
        try:
            self.regex = config['regex']
        except KeyError:
            self.regex = '^(?P<ip>\d+\.\d+\.\d+\.\d+).*(?P<method>(GET|PUT|POST|HEAD|DELETE|OPTIONS|CONNECT|PATCH|TRACE)) (?P<path>.*) HTTP.*\" (?P<status>\d+)'
        self.match = re.compile(self.regex)

    def tail_file(self):
        return Pygtail(self.file)

    def parse_log(self, log_line):
        """137.74.207.110 - - [10/Dec/2017:15:23:35 +0200] "GET /ar/occasions/details/2930 HTTP/1.1" 200 38658 "-" "Mozilla/5.0 (compatible; AhrefsBot/5.2; +http://ahrefs.com/robot/)"
            217.21.0.92 - - [10/Dec/2017:15:24:33 +0200] "GET / HTTP/1.1" 200 71483 "-" "check_http/v1.4.15"""
        m = re.match(self.match, log_line)
        if m:
            if m.group('status') in self.exclude_status:
                return None
            else:
                return '{},{},{},{}'.format(m.group('ip'), m.group('status'), m.group('method'),
                                        self.clean_url(m.group('path')))
        else:
            return None

    def clean_url(self, url):
        s_url = url.split('/')
        s_length = len(s_url)
        if s_length > 3:
            s_length = 3
        a = 1
        r_url = ""
        while a < s_length :
            r_url += s_url[a].split('?')[0] + "-"
            a += 1
        if r_url == '-':
            return "root"
        else:
            return r_url[:-1]


class MaxmindDB:

    """Warpper for maxmind db."""

    def __init__(self, config):
        self.db = config['maxminddb_path']
        self.readmax = maxminddb.open_database(self.db)

    def get_geodata(self, ip):
        geo = self.readmax.get(ip)
        try:
            city = geo['city']['names']['en']
        except KeyError:
            city = "None"
        except TypeError:
            city = "None"
        try:
            latitude = geo['location']['latitude']
        except KeyError:
            latitude = 0
        except TypeError:
            latitude = 0
        try:
            longitude = geo['location']['longitude']
        except KeyError:
            longitude = 0
        except TypeError:
            longitude = 0
        try:
            country_shortname = geo['registered_country']['iso_code']
        except KeyError:
            country_shortname = "None"
        except TypeError:
            country_shortname = "None"
        try:
            country_name = geo['registered_country']['names']['en']
        except KeyError:
            country_name = "none"
        except TypeError:
            country_name = "none"
        return {'city': city,
                'latitude': latitude,
                'longitude': longitude,
                'country_shortname': country_shortname,
                'country_name': country_name}