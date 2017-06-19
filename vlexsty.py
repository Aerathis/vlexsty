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

def build_resp(code, message=""):
    codeText = {
        200: 'OK',
        400: 'Bad Request',
        500: 'Internal Server Error'
    }
    return 'HTTP/1.1 ' + str(code) + ' ' + codeText[code] + '\nContent-Type: text/plain' + '\n\n' + message

def handle_client(conn, data):
    with open(LOG_PATH, 'a') as f:
        f.write(data + '\n')
    conn.send(build_resp(200))

def connect_client(conn):
    rawData = conn.read()
    clPos = rawData.lower().find('\r\ncontent-length: ')
    endHeaderPos = rawData.find('\r\n\r\n')
    if clPos >= 0 and endHeaderPos >= 0:
        endCl = rawData.find('\r\n', clPos + 17)
        cl = int(rawData[clPos + 17:endCl])
        bodyData = rawData[endHeaderPos+4:]
        if len(bodyData) == cl:
            handle_client(conn, bodyData)
        else:
            conn.send(build_resp(400, 'Missing data in request'))
    else:
        conn.send(build_resp(400, 'Missing Content length or body'))

while True:
    newsock, _ = bindsocket.accept()
    conn = ssl.wrap_socket(newsock, server_side=True, certfile=SERVER_CERT, keyfile=SERVER_KEY)

    try:
        connect_client(conn)
    finally:
        conn.shutdown(socket.SHUT_RDWR)
        conn.close()
