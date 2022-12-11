from network import Network

import socket
import sys

msgFromClient = "Hello TCP Server"

serverAddressPort = ("192.168.0.70", 1000)
bufferSize = 2048


class TCPClient(Network):
    def __init__(self):
        super(TCPClient, self).__init__()
        try:
            self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
            self.socket.settimeout(4)
            self.socket.connect(serverAddressPort)
            self.messageStr = ""

        except Exception as e:
            print(f"Failed to connect to remote: {e}")
            sys.exit(0)

    def send(self):
        try:
            if len(self.send_queue) > 0:
                message = self.send_queue.pop(0)
                print(f"Send: {message}")
                self.socket.sendto(message, serverAddressPort)
        except Exception as e:
            print(e)

    def _filter_duplicates(self, messageHdr, filter):
        for message in self.received_message_queue:
            if messageHdr in filter and messageHdr == message.headerStr:
                return True
        return False

    def receive(self):
        try:
            msgFromServer = self.socket.recv(bufferSize)
            print(msgFromServer)
            if b"+" in msgFromServer:
                print(msgFromServer)
                return
            self.messageStr += msgFromServer.decode()

        except socket.timeout:
            print("Recv timeout")
            return False
        self.parse_messages()
        return True
