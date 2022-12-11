def parse_message(message):
    print(message)
    parts = message.split(",")
    print(parts)
    parts[-1] = parts[-1]
    print(parts)
    return parts


class Message():
    def __init__(self, headerStr, dataList):
        self.headerStr = headerStr
        self.dataList = dataList

    def print(self):
        print(f"{self.headerStr}: {self.dataList}")


class Network():
    def __init__(self):
        self.remote_ready = False
        self.received_message_queue = []
        self.send_queue = []

    def add_to_send_queue(self, message, high_prio=False):
        if len(self.received_message_queue) == 0 and self.remote_ready:
            bytesToSend = str.encode(message)
            if high_prio:
                self.send_queue.insert(0, bytesToSend)
            else:
                self.send_queue.append(bytesToSend)

    def send(self):
        pass

    def receive(self):
        pass

    def pop_message(self):
        if len(self.received_message_queue) == 0:
            return None
        return self.received_message_queue.pop(0)

    def parse_messages(self):
        if '*' not in self.messageStr:
            return
        data = self.messageStr.split('*')
        for sentence in data:
            if len(sentence) == 0:
                continue
            if '$' in sentence:
                headerStr = sentence[0:5]
                dataList = parse_message(sentence[6:len(sentence)])
                if self._filter_duplicates(headerStr, ["$APNG", "$ARDY"]) is False:
                    print(f"Received sentence: ({sentence})")
                    self.received_message_queue.append(Message(headerStr, dataList))
                self.messageStr = self.messageStr[len(sentence) + 1:len(self.messageStr)]
            else:
                self.messageStr = self.messageStr[len(sentence) + 1:len(self.messageStr)]
