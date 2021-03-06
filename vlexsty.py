'''Simple module that writes out received crash reports to a log file to be forwarded'''
import socket
import ssl
import sys
import os
import errno
import traceback

ARGS = sys.argv[1:]

DEFAULT_CONF_PATH = '/etc/vlexsty.conf'

def build_config_map(values_list):
    '''Build up a configuration map from values read from the config file'''
    config_map = {}
    for config_key, config_value in values_list:
        config_map[config_key] = config_value
    return config_map

def read_conf(conf_path=None):
    '''Read the contents of the config file from either the given path or the default path'''
    if conf_path is None:
        if os.path.exists(DEFAULT_CONF_PATH) and os.path.isfile(DEFAULT_CONF_PATH):
            conf_path = DEFAULT_CONF_PATH
        else:
            print "No configuration file specified and no default file"
            sys.exit(1)

    with open(conf_path, 'r') as conf_file:
        conf_contents = conf_file.read()

    conf_values = [(k, v) for k, v in
                   [x.split('=') for x in conf_contents.split('\n') if len(x.split('=')) > 1]]

    return build_config_map(conf_values)


def usage():
    '''Print out the simple usage help message'''
    print """
Usage:
    sudo systemctl start vlexsty
"""

def build_resp(code, msg=''):
    '''Build a simple HTTP response string to send back to the client'''
    text = {
        200: 'OK',
        400: 'Bad Request',
        500: 'Internal Server Error'
    }
    return 'HTTP/1.1 {0} {1}\nContent-Type: text/plain\n\n{2}'.format(str(code), text[code], msg)

def handle_client(client, data, log_path):
    '''Handle the request from the client'''
    print data
    with open(log_path, 'a') as log_file:
        log_file.write(data + '\n')
    client.send(build_resp(200))

def connect_client(client, log_path):
    '''Establish the client connection and read data from the request'''
    data = client.read()
    length_pos = data.lower().find('\r\ncontent-length: ')
    if length_pos < 0:
        client.send(build_resp(400, 'No content length provided'))
        return
    content_length = int(data[length_pos + 18:data.find('\r\n', length_pos + 18)])
    print content_length
    end_header_pos = data.find('\r\n\r\n')
    print end_header_pos
    if end_header_pos == -1 or (end_header_pos + 4) >= len(data):
        raw_data = ''
    else:
        raw_data = data[end_header_pos + 4:]
    while len(raw_data) < content_length:
        chunk = client.read()
        raw_data += chunk
    handle_client(client, raw_data, log_path)

def start_server(provided_conf=None):
    '''Start server listening based on either provided config or default config'''
    config = read_conf(provided_conf)
    port = config['port']
    backlog = config['backlog']
    server_cert = config['server_cert']
    server_key = config['server_key']
    log_path = config['log_path']
    bindsocket = socket.socket()
    bindsocket.bind(('', int(port)))
    bindsocket.listen(int(backlog))
    while True:
        newsock, _ = bindsocket.accept()
        conn = None
        try:
            conn = ssl.wrap_socket(newsock, server_side=True, certfile=server_cert, keyfile=server_key, do_handshake_on_connect=False, suppress_ragged_eofs=True)
        except IOError, exc:
            print "Error trying to wrap connection", sys.exc_info()[0]
            traceback.print_exc()
            continue
        try:
            connect_client(conn, log_path)
            conn.shutdown(socket.SHUT_RDWR)
        except socket.error, exc:
            print exc
            continue
        finally:
            conn.close()

if len(sys.argv) > 1:
    if sys.argv[1].lower() == 'help':
        usage()
    else:
        start_server(sys.argv[1])
else:
    start_server()
