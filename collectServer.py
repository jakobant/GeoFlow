

from utils import MaxmindDB, YamlConfig, UDPServer, RedisClient
import threading

class SuperServer:

    """Init super server"""

    def __init__(self):
        self.config = YamlConfig('settings.yaml').get_config()
        self.readmax = MaxmindDB(self.config['module']['config'])
        self.server = UDPServer(int(self.config['module']['config']['udp_port']))
        self.r = RedisClient({'redis_server': '127.0.0.1'})
        self.counters = {}
        self.lock = threading.Lock()

    def main(self):
        self.counters = {}
        t = threading.Timer(0.1, self._send_to_redis)
        t.start()
        while True:
            data, address = self.server.get_messages()
            ip, status, method, path = data.decode().split(',')
            self.lock.acquire()
            try:
                self.counters['{}|{}|{}'.format(ip, status, method)] += 1
            except KeyError:
                self.counters['{}|{}|{}'.format(ip, status, method)] = 1
            self.lock.release()

    def _send_to_redis(self):
        print("Dumping counters")
        self.lock.acquire()
        for key in self.counters:
            iip, sstatus, mmethod = key.split('|')
            geo_data = self.readmax.get_geodata(iip)
            rdata = {
                'ip': iip,
                'status': sstatus,
                'method': mmethod,
                'path': '',
                'count': self.counters[key],
                'geo': geo_data
            }
            self.r.publish_to_topic('geo-data-flow', rdata)
        self.counters = {}
        self.lock.release()
        threading.Timer(0.1, self._send_to_redis).start()


if __name__ == "__main__":
    server = SuperServer()
    server.main()

