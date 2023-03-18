from network import Network

import serial


class SerialClient(Network):
    """! ASCII messaging client using Serial protocol
    See details in \a Network.
    """
    def __init__(self):
        super(SerialClient, self).__init__()
        self.serial_client = serial.Serial(port='/dev/ttyACM0', baudrate=115200, timeout=.1)
        self.messageStr = ""

    def send(self):
        """! Sends the first element in the message queue if the client is ready to send
        """
        try:
            if len(self.send_queue) > 0 and self.ready_to_send:
                self.last_sent = self.send_queue.pop(0)
                bytesToSend = self.encode(self.last_sent)
                print(f"Send: {bytesToSend}")
                self.serial_client.write(bytesToSend)
                self.ready_to_send = False
        except Exception as e:
            print(f"Error: {e}")

    def receive(self):
        """! Receives and decodes an ASCII message from the arduino.
        """
        try:
            msgFromServer = self.serial_client.readline()
            if msgFromServer != b"":
                if b"!!" in msgFromServer:
                    print(f"Feedback: {msgFromServer}")
                    return True
                self.remote_ready = True
                self.ready_to_send = True
            else:
                return False
            self.messageStr += msgFromServer.decode()
        except Exception as e:
            print(e)
            return False
        self.parse_messages()
        return True
