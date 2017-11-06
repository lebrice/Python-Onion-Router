class circuit_table():
    """
        kv table maintained by sender or node
        contains a list of circuit IDs that have been created, associated with the ip and port to contact
        format: ip:port | circID
    """

    table = {}

    def add_circuit_entry(self, ip, port, circID):
        index = format("{}:{}", ip, port)
        self.table[index] = circID   # packet builder prevents duplicate circIDs from being created

    def remove_circuit_entry(self, ip, port):
        index = format("{}:{}", ip, port)
        try:
            del self.table[index]
        except LookupError:
            print("ERROR    No such IP address in the key table; could not remove entry")

    def get_circID(self, ip, port):
        index = format("{}:{}", ip, port)
        try:
            return self.table[index]
        except LookupError:
            print("ERROR    No such IP address in the circuit table; could not return circuit ID")

    # needed for nodes that have both incoming and outgoing circIDs; better than maintaining two tables
    def get_address(self, circID):
        for k in self.table.keys():
            if self.table[k] == circID:
                return k
        print("ERROR    No such circuit ID in the circuit table; could not return IP address")

    def print_table(self):
        for k in self.table.keys():
            print(self.table[k])


class sender_key_table():
    """
        kv table maintained by sender
        contains all the symmetric keys that were sent to nodes along the path
        format: ip:port | key

    """

    table = {}

    def add_key_entry(self, ip, port, symmkey):
        index = format("{}:{}", ip, port)
        self.table[index] = symmkey

    def remove_key_entry(self, ip, port):
        index = format("{}:{}", ip, port)
        try:
            del self.table[index]
        except LookupError:
            print("ERROR    No such IP address in the key table; could not remove entry")

    def get_key(self, ip, port):
        index = format("{}:{}", ip, port)
        try:
            return self.table[index]
        except LookupError:
            print("ERROR    No such IP address in the key table; could not return key")

    def print_table(self):
        for k in self.table.keys():
            print(self.table[k])


class node_key_table():
    """
        kv table maintained by a node
        contains the key to use when a relay packet is received from a circuit ID
        format: received_from_circID | key
    """

    table = {}

    def add_key_entry(self, fromID, symmkey):
        self.table[fromID] = symmkey

    def remove_key_entry(self, fromID):
        try:
            del self.table[fromID]
        except LookupError:
            print("ERROR    No such IP address in the key table; could not remove entry")

    def get_key(self, fromID):
        try:
            return self.table[fromID]
        except LookupError:
            print("ERROR    No such IP address in the key table; could not return key")

    def print_table(self):
        for k in self.table.keys():
            print(self.table[k])


class node_relay_table():
    """
        kv table maintained by a node
        contains the routing information for relay of packets along circuits
        format: received_from_circID | send_to_circID
    """

    table = {}

    def add_relay_entry(self, fromID, toID):
        self.table[fromID] = toID

    def remove_relay_entry(self, fromID):
        try:
            del self.table[fromID]
        except LookupError:
            print("ERROR    No such IP address in the key table; could not remove entry")

    def get_dest_id(self, fromID):
        try:
            return self.table[fromID]
        except LookupError:
            print("ERROR    No such IP address in the key table; could not return key")

    def print_table(self):
        for k in self.table.keys():
            print(self.table[k])