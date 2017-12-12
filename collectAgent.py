import sys
from time import sleep

from utils import YamlConfig, HttpAgent, UDPClient

class SuperAgent:

    """"Agent collector"""

    def __init__(self):
        self.config = YamlConfig('settings.yaml').get_config()

    def http_main(self, config, demo):
        server = UDPClient(config)
        agent = HttpAgent(config)
        #Loop for ever and ever ever
        c = 0
        while True:
            for line in agent.tail_file():
                message = agent.parse_log(line)
                if message:
                    server.send_message(message)
                if demo and c > 50:
                    sleep(1)
                    c = 0
                c += 1
            sleep(1)

    def main(self):
        """Do some stuff"""
        if self.config['module']['demo'] == "true":
            demo = True
        else:
            demo = False
        if self.config['module']['name'] == "http":
            self.http_main(self.config['module']['config'], demo)
        if self.config['module']['name'] == "softflow":
            self.http_main(self.config['module']['name'])


if __name__ == "__main__":
    agent = SuperAgent()
    agent.main()
