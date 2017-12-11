import json
import tornadoredis
import tornado.ioloop
import tornado.web
import tornado.websocket


class IndexHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(request):
        request.render('index.html')

class WebSocketChatHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, *args, **kwargs):
        super(WebSocketChatHandler, self).__init__(*args,**kwargs)
        self.listen()

    def check_origin(self, origin):
        return True

    @tornado.gen.engine
    def listen(self):

        print('[*] WebSocketChatHandler opened')

        try:
            # This is the IP address of the DataServer
            self.client = tornadoredis.Client('127.0.0.1')
            self.client.connect()
            print('[*] Connected to Redis server')
            yield tornado.gen.Task(self.client.subscribe, 'netflow-map')
            self.client.listen(self.on_message)
        except Exception as ex:
            print('[*] Could not connect to Redis server.')
            print('[*] {}'.format(str(ex)))

    def on_close(self):
        print('[*] Closing connection.')

    # This function is called everytime a Redis message is received
    def on_message(self, msg):

        if len(msg) == 0:
            print("msg == 0\n")
            return None

        try:
            json_data = json.loads(msg.body)
        except Exception as ex:
            return None

        print(json_data)

        fat = json_data['fat']
        src_ip = json_data['src_ip']
        dst_ip = json_data['dst_ip']
        msg_to_send = {
                        'fat': fat,
                        'src_ip': src_ip,
                        'dst_ip': dst_ip
        }

        self.write_message(json.dumps(msg_to_send))


def main():
    # Register handler pages
    handlers = [
        (r'/websocket', WebSocketChatHandler),
        #(r'/static/(.*)', tornado.web.StaticFileHandldder, {'path': 'static'}),
        #(r'/flags/(.*)', tornado.web.StaticFileHandler, {'path': 'static/flags'}),
        (r'/', IndexHandler)
    ]

    # Define the static path
    # static_path = path.join( path.dirname(__file__), 'static' )

    # Define static settings
    settings = {
        # 'static_path': static_path
    }

    # Create and start app listening on port 8888
    try:
        app = tornado.web.Application(handlers, **settings)
        app.listen(8888)
        print('[*] Waiting on browser connections...')
        tornado.ioloop.IOLoop.instance().start()
    except Exception as appFail:
        print(appFail)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nSHUTTING DOWN')
        exit()
