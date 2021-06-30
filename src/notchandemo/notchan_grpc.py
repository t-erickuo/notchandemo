import grpc
import LightsaberService_pb2_grpc as service


class NotificationChannel:

    def __init__(self, host):
        self.host = host
        self._stub = None

    def connect(self):
        channel = grpc.insecure_channel(self.host)
        self._stub = service.LightsaberServiceStub(channel)

    def run(self):
        self.connect()
        for notification in self._stub.SubscribeSession('randomsession'):
            yield notification
        
if __name__ == '__main__':
    channel = NotificationChannel('localhost')
    channel.run()