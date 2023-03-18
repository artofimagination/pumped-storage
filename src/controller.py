from network import Message


class Controller():
    """! Simple relay controller, that sends control commands to the Arduino.
    """
    REQUEST_SET_PUMP_RELAY_STATE = "$RPMP"
    REQUEST_SET_VALVE_RELAY_STATE = "$RVLV"
    REQUEST_SET_SOLAR_RELAY_STATE = "$RSLR"
    REQUEST_SET_GENERATOR_RELAY_STATE = "$RGNR"
    REQUEST_SET_MANUAL_MODE = "$RMNL"

    def __init__(self, tcp_client):
        self.manual = True
        self.tcp_client = tcp_client

    def _set_relay_state(self, request_header, state):
        stateInt = 0
        if state:
            stateInt = 1
        message = Message(request_header, [stateInt])
        self.tcp_client.add_to_send_queue(message, True)

    def set_manual_state(self, state):
        if self.manual != state:
            self.manual = state
            return True
        return False

    def set_manual(self, state):
        if self.set_manual_state(state):
            self._set_relay_state(self.REQUEST_SET_MANUAL_MODE, state)

    def set_pump_remote(self, state):
        self._set_relay_state(self.REQUEST_SET_PUMP_RELAY_STATE, state)

    def set_valve_remote(self, state):
        self._set_relay_state(self.REQUEST_SET_VALVE_RELAY_STATE, state)

    def set_solar_remote(self, state):
        self._set_relay_state(self.REQUEST_SET_SOLAR_RELAY_STATE, state)

    def set_generator_remote(self, state):
        self._set_relay_state(self.REQUEST_SET_GENERATOR_RELAY_STATE, state)
