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
import math
import os
import shutil
import socket
import threading
try:
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from tkinter import Tk, Frame, Label, BitmapImage
except ImportError:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
    from Tkinter import Tk, Frame, Label, BitmapImage
import pyqrcode


class SingleFileServer(HTTPServer):
    def __init__(self, server_address, RequestHandlerClass, file_path):
        self.file_path = file_path
        HTTPServer.__init__(self, server_address, RequestHandlerClass)

    def finish_request(self, request, client_address):
        self.RequestHandlerClass(request, client_address, self, self.file_path)


class SingleFileRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server, file_path):
        self.file_path = file_path
        BaseHTTPRequestHandler.__init__(self, request, client_address, server)

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        try:
            f = open(self.file_path, 'rb')
        except:
            self.send_error(404, 'File not found')
            return
        self.send_response(200, 'OK')
        self.send_header('Content-Type', 'application/octet-stream')
        self.send_header('Content-Length', os.fstat(f.fileno()).st_size)
        self.end_headers()
        try:
            shutil.copyfileobj(f, self.wfile)
        except:
            pass
        f.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Serve a CIA file to FBI via a QR code.')
    parser.add_argument('-t', action='store_true', help='Display QR code in terminal instead of using a GUI.')
    parser.add_argument('cia', help='CIA file to be serverd.')
    args = parser.parse_args()
    server = SingleFileServer(('', 8080), SingleFileRequestHandler, args.cia)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()
    qr = pyqrcode.create('http://{}:{}/installer.cia'.format(socket.gethostbyname(server.server_name), server.server_port))
    if args.t:
        print(qr.terminal())
        print('Serving file: {}'.format(os.path.abspath(args.cia)))
        try:
            raw_input('Press the Enter key to quit.')
        except NameError:
            input('Press the Enter key to quit.')
    else:
        root = Tk()
        root.title('FBI QR Code Install')
        main_frame = Frame(root)
        main_frame.pack()
        qr_bitmap = BitmapImage(data=qr.xbm(scale=8), foreground='black', background='white')
        qr_label = Label(main_frame, image=qr_bitmap)
        qr_label.pack()
        msg_label = Label(main_frame, text='Serving file: {}'.format(os.path.abspath(args.cia)))
        msg_label.pack()
        root.mainloop()
    server.shutdown()

