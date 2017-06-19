import socket, ssl, sys

args = sys.argv[1:]

PORT = None
BUFFERLEN = None
SERVER_CERT = None
SERVER_KEY = None
LOG_PATH = None


if len(args) > 0 and args[0].lower() == 'help':
    print """
Usage:
    python vlexsty.py (LISTEN_PORT) (BACKLOG_SIZE) (PATH_TO_SERVER_CERTIFICATE) (PATH_TO_SERVER_KEY) (LOG_PATH)
    """
    sys.exit(0)
else:
    if len(args) == 5:
        PORT = int(args[0])
        BUFFERLEN = int(args[1])
        SERVER_CERT = args[2]
        SERVER_KEY = args[3]
        LOG_PATH = args[4]
    else:
        print """
Usage:
    python vlexsty.py (LISTEN_PORT) (BACKLOG_SIZE) (PATH_TO_SERVER_CERTIFICATE) (PATH_TO_SERVER_KEY) (LOG_PATH)
    """
        sys.exit(1)

bindsocket = socket.socket()
bindsocket.bind(('', PORT))
bindsocket.listen(BUFFERLEN)

def handle_client(conn, data):
    with open(LOG_PATH, 'a') as f:
        f.write(data + '\n')

def connect_client(conn):
    data = conn.read()
    while data:
        handle_client(conn, data)
        data = conn.read()

while True:
    newsock, _ = bindsocket.accept()
    conn = ssl.wrap_socket(newsock, server_side=True, certfile=SERVER_CERT, keyfile=SERVER_KEY)

    try:
        connect_client(conn)
    finally:
        conn.shutdown(socket.SHUT_RDWR)
        conn.close()
