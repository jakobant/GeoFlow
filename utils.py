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
        self.json_ip = config['json_ip']
        self.json_status = config['json_status']
        self.json_request = config['json_request']
        try:
            self.regex = config['regex']
        except KeyError:
            self.regex = '^(?P<ip>\d+\.\d+\.\d+\.\d+).*(?P<method>(GET|PUT|POST|HEAD|DELETE|OPTIONS|CONNECT|PATCH|TRACE)) (?P<path>.*) HTTP.*\" (?P<status>\d+)'
        self.match = re.compile(self.regex)

    def tail_file(self):
        return Pygtail(self.file)

    def get_tag(self, log, tags):
        clean = log
        for node in tags['path']:
            if node in clean:
                clean = clean[node]
            else:
                clean = None
        return clean

    def parse_log(self, log_line):
        """137.74.207.110 - - [10/Dec/2017:15:23:35 +0200] "GET /ar/occasions/details/2930 HTTP/1.1" 200 38658 "-" "Mozilla/5.0 (compatible; AhrefsBot/5.2; +http://ahrefs.com/robot/)"
            217.21.0.92 - - [10/Dec/2017:15:24:33 +0200] "GET / HTTP/1.1" 200 71483 "-" "check_http/v1.4.15
        { "@timestamp": "2017-12-11T14:00:01+00:00", "geoip.country_name": "Australia", "geoip.country_code": "AU", "geoip.location": { "lat": "-33.2744", "lon": "151.5461" }, "@source_host": "public-dispatcher-deployment-1211055930-28cjc", "@fields": { "remote_addr": "1.43.193.104", "upstream_addr": "172.16.108.209:80", "request_length": 2774, "upstream_response_time": 0.510, "remote_user": "-", "body_bytes_sent": 1532, "request_time": 0.512, "status": "200", "request": "GET /rest/tempo-timesheets/3/period/ HTTP/1.1", "request_method": "GET", "http_referrer": "https://app.tempo.io/timesheets/jira/agile-issue-panel/NA/157541/NA-109/?can_log_work_for_others=false&can_set_billable_hours=false&can_view_all_worklogs=true&is_jira_admin=false&is_tempo_account_admin=false&is_tempo_admin=false&is_tempo_team_admin=true&is_tempo_timetracking=true&perm_delete_all_worklogs=true&perm_delete_own_worklogs=true&perm_edit_all_worklogs=false&perm_edit_own_worklogs=true&perm_work_on_issues=true&tz=Europe%2FMinsk&loc=en-US&user_id=igor.trandafilov&user_key=i.trandafilov&xdm_e=https%3A%2F%2Fisportal.atlassian.net&xdm_c=channel-is.origo.jira.tempo-plugin__tempo-ghx-issue-panel-worklogs&cp=&xdm_deprecated_addon_key_do_not_use=is.origo.jira.tempo-plugin&lic=active&cv=1.3.392&jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJpLnRyYW5kYWZpbG92IiwicXNoIjoiMGIxMzc2ODRmNWRlMWE0ZDQ5OGI5Mjc1ZGQ3MTI2YWNhNTUzMjRhMmYxMzRiMjdhMzBlMzYzMjM5ODhjZjMxNSIsImlzcyI6ImppcmE6MTEwMDEyMjUiLCJjb250ZXh0Ijp7InVzZXIiOnsidXNlcktleSI6ImkudHJhbmRhZmlsb3YiLCJ1c2VybmFtZSI6Imlnb3IudHJhbmRhZmlsb3YiLCJkaXNwbGF5TmFtZSI6Iklnb3IgVHJhbmRhZmlsb3YifX0sImV4cCI6MTUxMzAwMDk3OSwiaWF0IjoxNTEzMDAwNzk5fQ.-nfpZVHQqfuKa9sQnnfI7zfnsA8mhCxReKmsoiC4XRQ", "tempo_request_id": "1513000800915970667ea94acf18928a", "tenant_id": "6a3b6afd-acb2-4cd0-afcb-680ab6687556", "levelname": "INFO", "http_user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36" } }"""
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
