def parse_message(message):
    parts = message.split(",")
    parts[-1] = parts[-1]
    return parts


class Message():
    def __init__(self, headerStr, dataList):
        self.headerStr = headerStr
        self.dataList = dataList

    def print(self):
        print(f"{self.headerStr}: {self.dataList}")


class Network():
    """! ASCII messaging client base class.
    This is a very immature implementation. ASCII should be replaced with binary data.

    Messages are sent only if there was a feedback from the arduino about the previous message.
    Until then messages are queued.
    """
    def __init__(self):
        self.remote_ready = False
        self.ready_to_send = True
        self.received_message_queue = []
        self.send_queue = []

    def add_to_send_queue(self, message, high_prio=False):
        """! Adds the message to the queue. Also filters duplicates and blacklisted messages.
        """
        if self._filter_send_duplicates(message.headerStr, []) is False and self.remote_ready:
            if high_prio:
                self.send_queue.insert(0, message)
            else:
                self.send_queue.append(message)

    def encode(self, message):
        """! Encodes the data into specific ASCII format
        Example: $MSGID,d1,d2,d3*
        """
        encodedMessageStr = f"{message.headerStr}"
        for data in message.dataList:
            encodedMessageStr += f",{data}"
        encodedMessageStr += "*"
        return str.encode(encodedMessageStr)

    def send(self):
        pass

    def receive(self):
        pass

    def pop_message(self):
        """! Pops the odlest message in the receive queue for process.
        """
        if len(self.received_message_queue) == 0:
            return None
        return self.received_message_queue.pop(0)

    def parse_messages(self):
        """! Parses ASCII message into data
        """
        if '*' not in self.messageStr:
            return
        data = self.messageStr.split('*')
        for sentence in data:
            if len(sentence) == 0:
                continue
            if '$' in sentence:
                headerStr = sentence[0:5]
                dataList = parse_message(sentence[6:len(sentence)])
                if self._filter_received_duplicates(headerStr, ["$ARDY"]) is False:
                    self.received_message_queue.append(Message(headerStr, dataList))
                self.messageStr = self.messageStr[len(sentence) + 1:len(self.messageStr)]
            else:
                self.messageStr = self.messageStr[len(sentence) + 1:len(self.messageStr)]

    def _filter_received_duplicates(self, messageHdr, filter):
        for message in self.received_message_queue:
            if messageHdr in filter and messageHdr == message.headerStr:
                return True
        return False

    def _filter_send_duplicates(self, messageHdr, filter):
        for message in self.send_queue:
            print(message.headerStr)
            if messageHdr in filter and messageHdr == message.headerStr:
                return True
        return False
