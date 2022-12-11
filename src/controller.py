

class Controller():
    REQUEST_SET_PUMP_RELAY_STATE = "$RPMP"
    REQUEST_SET_VALVE_RELAY_STATE = "$RVLV"
    REQUEST_SET_SOLAR_RELAY_STATE = "$RSLR"
    REQUEST_SET_GENERATOR_RELAY_STATE = "$RGNR"

    def __init__(self, tcp_client):
        self.pump_relay_state = False
        self.valve_relay_state = False
        self.tcp_client = tcp_client

    def _set_relay_state(self, request_header, state):
        stateInt = 0
        if state:
            stateInt = 1
        message = f"{request_header},{stateInt}*"
        self.tcp_client.add_to_send_queue(message, True)

    def set_pump(self, state):
        if self.pump_relay_state != state:
            self.pump_relay_state = state
        self._set_relay_state(self.REQUEST_SET_PUMP_RELAY_STATE, state)

    def set_valve(self, state):
        if self.valve_relay_state != state:
            self.valve_relay_state = state
        self._set_relay_state(self.REQUEST_SET_VALVE_RELAY_STATE, state)

    def set_solar(self, state):
        if self.valve_relay_state != state:
            self.valve_relay_state = state
        self._set_relay_state(self.REQUEST_SET_SOLAR_RELAY_STATE, state)

    def set_generator(self, state):
        if self.valve_relay_state != state:
            self.valve_relay_state = state
        self._set_relay_state(self.REQUEST_SET_GENERATOR_RELAY_STATE, state)
