# Copyright (c) 2022, W. M. Keck Observatory
# All rights reserved.

# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. 



from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
from ETC import exposure_time_calculator
import json
from re import sub  # Processing regular expressions
from base64 import b64decode
from numpy import NaN, isnan
from datetime import datetime
from os import getpid
from sys import argv


hostName = "0.0.0.0"
serverPort = 50006 



def process_request(query):
    if len(query) == 0:
        return '', True

    try:
        # Informative error if no return values specified
        if not 'return' in query.keys():
            raise ValueError('Must specify return values, i.e. return=[exposure]')

        # Remove return values from query
        if isinstance(query['return'], list):
            return_vals = { x:[] for x in query['return'] }
        else:
            return_vals = { query['return'] : [] }
        del query['return']

        etc.set_parameters(query)
        # Get the requested values
        for key in return_vals.keys():
            if key == 'parameters':
                # If parameters were requested, retrieve them
                return_vals[key] = etc.get_parameters()
            elif key == 'nonlinear_depth_adu':
                return_vals[key] = [etc.instrument.nonlinear_depth.to('adu').value]
            else:
                return_vals[key] = vars(etc)[key].value.tolist()
                # Coerce to valid JSON format by converting NaN to string
                return_vals[key] = replaceNaN(return_vals[key], 'NaN')

        return return_vals, False
    except Exception as e:
        # For a more informative (but messier) error msg, use repr(e)
        return f'An error occured while processing your request<br>{str(e)}<br><br>', True

def text2html(text):
    text = text.replace('&', '&#38;')
    text = text.replace(' ', '&nbsp;')
    text = text.replace('\t', '&nbsp'*4)
    text = text.replace('\n', '<br>')
    return '<html><body style="font-family: monospace;">' + text + '</body></html>'

def replaceNaN(array, replacement):
    new_array = array
    for idx, item in enumerate(array):
        if isinstance(item, list):
            new_array[idx] = replaceNaN(item, replacement)
        else:
            new_array[idx] = replacement if isnan(item) else item
    return new_array

def query2dict(query):
    query = query.split("&")
    # Remove base64 encoded content (which is padded w/ "=") so that it doesn't break parsing
    b64 = [q for q in query if 'b64=' in q]
    query = [q for q in query if 'b64=' not in q]
    # Parse query
    query = dict(q.split("=") for q in query)
    # Convert lists from string to list
    for key, val in query.items():
        if val.startswith('[') and val.endswith(']'):
            query[key] = [x.strip() for x in val[1:-1].split(',')]
    # Add in removed base 64 content
    for b in b64:
        query[b.split('b64=')[0]+'b64'] = b.split('b64=')[-1]

    return query
           

def sanitize_input(text):
    # Allowed characters are alphanumerics and . = [ ] - / ( ) & + _ ,
    whitelist = r'a-zA-Z0-9\.\=\[\]\-\/()&+_,'
    # Negate the list of allowed characters
    not_whitelist = f'[^{whitelist}]'
    # Remove all non-allowed characters from string
    return sub(not_whitelist,'', text)



class APIServer(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def respond(self, query):
        response, error = process_request(query)
        if len(response) == 0:
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(bytes(self.usage, 'utf-8'))
        elif error:
            self.send_response(400)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(bytes(response, 'utf-8'))
        else:
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(bytes(json.dumps(response, ensure_ascii=False), 'utf-8'))

    def do_POST(self):
        with open('src/static/api_instructions.txt', 'r') as file:
            self.usage = text2html(file.read())

        try:
            query = self.rfile.read( int(self.headers.get('Content-Length')) ).decode('utf-8')
            query = sanitize_input(query)
            query = query2dict(query)
        except:
            query = {}
        
        self.respond(query)    
        # Reset etc for future API call
        etc.reset_parameters()

    def do_GET(self):
        with open('src/static/api_instructions.txt', 'r') as file:
            self.usage = text2html(file.read())

        try:
            query = urlparse(self.path).query
            query = sanitize_input(query)
            query = query2dict(query)
        except:
            query = {}
            
        self.respond(query)
        # Reset etc for future API call
        etc.reset_parameters()


if __name__ == "__main__":

    # Handle command line argument to specify port
    if len(argv) > 2:
        print('Invalid number of arguments, must be 0 or 1')
        exit(-1)
    elif len(argv) == 2:
        if argv[-1].isdigit():
            serverPort = int(argv[-1])
        else:
            print('Invalid port number', argv[-1])
            exit(-1)


    etc = exposure_time_calculator()  # Initialize etc

    webServer = HTTPServer((hostName, serverPort), APIServer)
    print(f'{hostName}:{serverPort} - - [{datetime.now().strftime("%d/%b/%Y %H:%M:%S")}] "Server started" {getpid()} -')

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print(f'{hostName}:{serverPort} - - [{datetime.now().strftime("%d/%b/%Y %H:%M:%S")}] "Server stopped" {getpid()} -')