from network import Network

import serial


class SerialClient(Network):
    def __init__(self):
        super(SerialClient, self).__init__()
        self.serial_client = serial.Serial(port='/dev/ttyACM0', baudrate=115200, timeout=.1)
        self.messageStr = ""

    def send(self):
        try:
            if len(self.send_queue) > 0:
                message = self.send_queue.pop(0)
                print(f"Send: {message}")
                self.serial_client.write(bytes(message, 'utf-8'))
        except Exception as e:
            print(e)

    def receive(self):
        try:
            msgFromServer = self.serial_client.readline()
            print(msgFromServer)
            if b"+" in msgFromServer:
                print(msgFromServer)
                return
            self.messageStr += msgFromServer.decode()
        except Exception as e:
            print(e)
            return False
        self.parse_messages()
        return True
