import json

# try to create a json file, and write to it

new_entry = {
    'ip'    : "127.0.0.1",
    'port' 	: "12346",
    'public_exp'	: 65357,
    'modulus'		: 555
}

# try to open file
try:
    f = open('TEST.json', 'r')
except FileNotFoundError:
    f = open('TEST.json', 'x')
    new = {'nodes in network' : [{
        'ip': "127.0.0.1",
        'port': "12345",
        'public_exp': 222,
        'modulus': 222
    }]}
    json.dump(new, f)
    f.close()

    f = open('test.json', 'r')

data = json.load(f)
data['nodes in network'].append(new_entry)

test_ip = "127.0.0.1"
test_port = "12345"

updated = 0
for n in data['nodes in network']:
    if n['ip'] == test_ip and n['port'] == test_port:
        n['ip'] = "CHANGED IP"
        n['port'] = "CHANGED PORT"
        updated = 1

with open('test.json', 'w') as f:
    json.dump(data, f)
    f.close()
