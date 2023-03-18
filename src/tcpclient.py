from network import Network

import socket
import sys

msgFromClient = "Hello TCP Server"

serverAddressPort = ("192.168.0.70", 1000)
bufferSize = 2048


class TCPClient(Network):
    """! ASCII messaging client using TCP protocol
    See details in \a Network.
    """
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
        """! Sends the first element in the message queue if the client is ready to send
        """
        try:
            if len(self.send_queue) > 0 and self.ready_to_send:
                self.last_sent = self.send_queue.pop(0)
                bytesToSend = self.encode(self.last_sent)
                print(f"Send: {bytesToSend}")
                self.socket.sendto(bytesToSend, serverAddressPort)
                self.ready_to_send = False
        except Exception as e:
            print(e)

    def receive(self):
        """! Receives and decodes an ASCII message from the arduino.
        """
        try:
            msgFromServer = self.socket.recv(bufferSize)
            if msgFromServer != b"":
                if b"!!" in msgFromServer or b"++" in msgFromServer:
                    print(f"Feedback: {msgFromServer}")
                    return True
                self.remote_ready = True
                self.ready_to_send = True
            else:
                return False
            self.messageStr += msgFromServer.decode()

        except socket.timeout:
            print("Recv timeout")
            return False
        self.parse_messages()
        return True
