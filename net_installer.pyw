#!/usr/bin/python

# Copyright 2016 Seth VanHeulen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function
import argparse
import os
import socket
import struct
import threading
try:
    from http.server import SimpleHTTPRequestHandler, HTTPServer
    from tkinter import Tk, Frame, Label, BitmapImage
    from urllib.parse import quote
except ImportError:
    from BaseHTTPServer import HTTPServer
    from SimpleHTTPServer import SimpleHTTPRequestHandler
    from Tkinter import Tk, Frame, Label, BitmapImage
    from urllib import quote
    input = raw_input


class LimitedHTTPServer(HTTPServer):
    def __init__(self, server_address, RequestHandlerClass, file_list):
        self._file_list = file_list
        HTTPServer.__init__(self, server_address, RequestHandlerClass)

    def finish_request(self, request, client_address):
        self.RequestHandlerClass(request, client_address, self, self._file_list)


class LimitedHTTPRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, request, client_address, server, file_list):
        self._file_list = file_list
        SimpleHTTPRequestHandler.__init__(self, request, client_address, server)

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        try:
            i = int(self.path.lstrip('/'))
            self.path = '/{}'.format(self._file_list[i].replace(os.sep, '/'))
        except (ValueError, IndexError):
            self.send_error(404, "File not found")
        else:
            SimpleHTTPRequestHandler.do_GET(self)


def display_error(message, cli=False):
    if cli:
        print('error:', message)
    else:
        root = Tk()
        root.title('Error')
        message_label = Label(root, text=message)
        message_label.pack()
        root.mainloop()

def display_qr(qr_code, input_path, file_list, cli=False):
    if cli:
        print(qr_code.terminal())
        print('Serving from path: {}'.format(input_path))
        print('Serving files:\n    {}'.format('\n    '.join(file_list)))
        try:
            input('Press the Enter key to quit.')
        except:
            return
    else:
        root = Tk()
        root.title('FBI QR Code Install')
        main_frame = Frame(root)
        main_frame.pack()
        qr_bitmap = BitmapImage(data=qr_code.xbm(scale=6), foreground='black', background='white')
        qr_label = Label(main_frame, image=qr_bitmap)
        qr_label.pack()
        path_label = Label(main_frame, text='Serving from path:\n{}'.format(input_path))
        path_label.pack()
        files_label = Label(main_frame, text='Serving files:\n{}'.format('\n'.join(file_list)))
        files_label.pack()
        root.mainloop()

def send_urls(urls, remote_ip_addr, input_path, file_list):
    print('Serving from path: {}'.format(input_path))
    print('Serving files:\n    {}'.format('\n    '.join(file_list)))
    print('Sending file list ...')
    try:
        conn = socket.create_connection((remote_ip_addr, 5000))
    except:
        print('error: Unable to connect.')
        return
    try:
        urls = urls.encode()
        conn.sendall(struct.pack('!I', len(urls)) + urls)
    except:
        print('error: Unable to send file list.')
        conn.close()
        return
    print('Waiting for install to complete ...')
    try:
        ack = conn.recv(1)
    except:
        print('error: Unable to recieve acknowledge.')
        return

def main(input_path, ip_port=8080, cli=False, remote_ip_addr=None):
    if not os.path.exists(input_path):
        display_error('The input path does not exist: {}'.format(input_path), cli)
        return
    file_list = []
    if os.path.isfile(input_path) and input_path.lower().endswith(('.cia', '.tik')):
        file_list.append(os.path.basename(input_path))
        input_path = os.path.dirname(input_path)
    elif os.path.isdir(input_path):
        for dirpath, dirnames, filenames in os.walk(input_path):
            dirpath = dirpath.replace(input_path, '', 1).lstrip(os.sep)
            file_list.extend([os.path.join(dirpath, f) for f in filenames if f.lower().endswith(('.cia', '.tik'))])
    if len(file_list) == 0:
        display_error('No CIA/TIK files were found at the input path: {}'.format(input_path), cli)
        return
    input_path = os.path.abspath(input_path)
    os.chdir(input_path)
    server = LimitedHTTPServer(('', ip_port), LimitedHTTPRequestHandler, file_list)
    ip_addr = socket.gethostbyname(server.server_name)
    urls = '\n'.join(['{}:{}/{}'.format(ip_addr, ip_port, i) for i in range(len(file_list))])
    qr_code = None
    if remote_ip_addr is None:
        try:
            import pyqrcode
            qr_code = pyqrcode.create(urls)
        except ImportError:
            display_error('The PyQRCode module is required to generate a QR code.', cli)
            return
        except ValueError:
            display_error('The combined file paths are too large to fit in a QR code.', cli)
            return
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()
    if remote_ip_addr is None:
        display_qr(qr_code, input_path, file_list, cli)
    else:
        send_urls(urls, remote_ip_addr, input_path, file_list)
    server.shutdown()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Serve CIA/TIK files to FBI via a QR code.')
    parser.add_argument('-p', '--port', default=8080, type=int, help='The port to listen on.')
    parser.add_argument('-t', action='store_true', help='Display QR code in the terminal instead of using a GUI.')
    parser.add_argument('--send', metavar='HOST', help='Send the file list to this IP instead of displaying a QR code.')
    parser.add_argument('input', help='A folder containing CIA/TIK files or a single CIA/TIK file.')
    args = parser.parse_args()
    main(args.input, args.port, args.t, args.send)

