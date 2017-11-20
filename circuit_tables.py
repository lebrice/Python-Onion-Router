class circuit_table():
    """
        kv table maintained by sender or node
        contains a list of circuit IDs that have been created, associated with the ip and port to contact
        format: ip:port | circID
    """
    def __init__(self):
        self.table = {}

    def add_circuit_entry(self, ip, port, circID):
        index = "{}:{}".format(ip, port)
        self.table[index] = circID   # packet builder prevents duplicate circIDs from being created

    def remove_circuit_entry(self, ip, port):
        index = "{}:{}".format(ip, port)
        try:
            del self.table[index]
        except LookupError:
            print("ERROR    No such IP address in the key table; could not remove entry")
            return -1

    def get_circID(self, ip, port):
        index = "{}:{}".format(ip, port)
        try:
            return self.table[index]
        except LookupError:
            print("ERROR    No such IP address in the circuit table; could not return circuit ID")
            return -1

    # needed for nodes that have both incoming and outgoing circIDs; better than maintaining two tables
    def get_address(self, circID):
        print(circID)
        #this is printed when the table is empty, even for first circuit that is built
        if not self.table:
            return -1
        for k in self.table.keys():
            if self.table[k] == circID:
                return k
        print("ERROR    No such circuit ID in the circuit table; could not return IP address")
        return -1

    def get_length(self):
        return len(self.table)

    def print_table(self):
        for k in self.table.keys():
            print(k.format(": ", self.table[k]))


class sender_key_table():
    """
        kv table maintained by sender
        contains all the symmetric keys that were sent to nodes along the path
        format: initial_circID:node # | key
            ex: bob is the first node (id=10), carol the second node (id unknown to sender)
                10:1 | bob shared key
                10:2 | carol shared key

    """

    def __init__(self):
        self.table = {}

    def add_key_entry(self, circID, nodeNo, symmkey):
        index = "{}:{}".format(circID, nodeNo)
        self.table[index] = symmkey

    def remove_key_entry(self, circID, nodeNo):
        index = "{}:{}".format(circID, nodeNo)
        try:
            del self.table[index]
        except LookupError:
            print("ERROR    No such node address in the key table; could not remove entry")
            return -1

    def get_key(self, circID, nodeNo):
        index = "{}:{}".format(circID, nodeNo)
        try:
            return self.table[index]
        except LookupError:
            print("ERROR    No such node address in the key table; could not return key")
            return -1

    def print_table(self):
        for k in self.table.keys():
            print(self.table[k])


class node_key_table():
    """
        kv table maintained by a node
        contains the key to use when a relay packet is received from a circuit ID
        format: received_from_circID | key
    """

    def __init__(self):
        self.table = {}

    def add_key_entry(self, fromID, symmkey):
        self.table[fromID] = symmkey

    def remove_key_entry(self, fromID):
        try:
            del self.table[fromID]
        except LookupError:
            print("ERROR    No such IP address in the key table; could not remove entry")
            return -1

    def get_key(self, fromID):
        try:
            return self.table[fromID]
        except LookupError:
            print("ERROR    No such IP address in the key table; could not return key")
            return -1

    def print_table(self):
        for k in self.table.keys():
            print(self.table[k])


class node_relay_table():
    """
        kv table maintained by a node
        contains the routing information for relay of packets along circuits
        format: received_from_circID | send_to_circID
    """

    def __init__(self):
        self.table = {}

    def add_relay_entry(self, fromID, toID):
        self.table[fromID] = toID

    def remove_relay_entry(self, fromID):
        try:
            del self.table[fromID]
        except LookupError:
            print("ERROR    No such circID in the key table; could not remove entry")
            return -1

    def get_dest_id(self, fromID):
        # empty table triggers error message
        if not self.table:
            return -1
        try:
            return self.table[fromID]
        except LookupError:
            print("ERROR    No such circID in the key table; could not return key")
            return -1

    def get_from_id(self, destID):
        #empty table triggers error message
        if not self.table:
            return -1
        for k in self.table.keys():
            if self.table[k] == destID:
                return k

        print("ERROR    No such circID in the key table; could not return key")
        return -1

    def get_length(self):
        return len(self.table)

    def print_table(self):
        for k in self.table.keys():
            print(self.table[k])