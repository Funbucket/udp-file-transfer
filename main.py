import os
import socket

FLAGS = _ = None
DEBUG = False


def get_filedict(rootpath):
    files = {}
    with os.scandir(rootpath) as it:
        for entry in it:
            if not entry.name.startswith('.') and entry.is_file():
                info = get_fileinfo(entry.path)
                info['path'] = entry.path
                files[entry.name] = info
    return files


def get_fileinfo(path):
    size = 0
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(FLAGS.mtu)
            chunk_size = len(chunk)
            if chunk_size == 0: # if not data:
                break
            size = size + chunk_size
    return {'size': size}


def main():
    if DEBUG:
        print(f'Parsed arguments {FLAGS}')
        print(f'Unparsed arguments {_}')

    files = get_filedict(FLAGS.files)
    if DEBUG:
        print(f'Ready to file transfer')
        for key, value in files.items():
            print(f'{key}: {value}')

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((FLAGS.address, FLAGS.port))
    print(f'Listening on {sock}')
    while True:
        try:
            data, client = sock.recvfrom(FLAGS.mtu)
            data = data.decode('utf-8')
            data = data.split(' ')

            if len(data) < 2:
                response = 'Error'
                sock.sendto(response.encode('utf-8'), client)
                continue

            command = data[0].upper()
            target = ' '.join(data[1:])
            print(f'{command} {target} from {client}')

            if target not in files.keys():
                print(f'{target} was not found (requested by {client})')
                response = '404 Not Found'
                sock.sendto(response.encode('utf-8'), client)
                continue

            info = files[target]
            path = info['path']
            size = info['size']
            transferring = True

            if command == 'INFO':
                size_b = str(size).encode('utf-8')
                sock.sendto(size_b, client)
            elif command == 'DOWNLOAD':
                with open(path, 'rb') as output:
                    while transferring:
                        data = output.read(FLAGS.mtu)
                        if not data:
                            transferring = False
                            continue
                        sock.sendto(data, client)
            print(f'File transfer complete {target}')
        except KeyboardInterrupt:
            print(f'Shutting down... {sock}')
            break


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true',
                        help='The present debug message')
    parser.add_argument('--address', type=str, default='127.0.0.1',
                        help='The address to serve service')
    parser.add_argument('--port', type=int, default=38442,
                        help='The port to serve service')
    parser.add_argument('--mtu', type=int, default=1400,
                        help='The maximum transmission unit')
    parser.add_argument('--files', type=str, default='./files',
                        help='The file directory path')

    FLAGS, _ = parser.parse_known_args()
    DEBUG = FLAGS.debug

    FLAGS.files = os.path.abspath(os.path.expanduser(FLAGS.files))

    main()
