from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
from calculator.ETC import exposure_time_calculator
import json
from re import sub  # Processing regular expressions
from base64 import b64decode
from numpy import NaN, isnan


hostName = "0.0.0.0"
serverPort = 8080

# TODO -- initialize etc when beginning server, then reset it in between requests
def process_request(query):
    if len(query) == 0:
        return '', True

    try:
        # Remove return values from query
        if isinstance(query['return'], list):
            return_vals = { x:[] for x in query['return'] }
        else:
            return_vals = { query['return'] : [] }
        del query['return']
        etc = exposure_time_calculator()  # Initialize etc
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
                # Coerce to valid JSON format by converting NaN to null
                return_vals[key] = replaceNaN(return_vals[key], 'NaN')

        return return_vals, False
    except Exception as e:
        return f'An error occured while processing your request<br>{e}<br><br>', True

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
    query = dict(qc.split("=") for qc in query.split("&"))
    # Convert lists from string to list
    for key, val in query.items():
        if val.startswith('[') and val.endswith(']'):
            query[key] = [x.strip() for x in val[1:-1].split(',')]
    return query
           

def sanitize_input(text):
    # Allowed characters are alphanumerics and . = [ ] - ( ) & + _ ,
    whitelist = r'a-zA-Z0-9\.\=\[\]\-()&+_,'
    # Negate the list of allowed characters
    not_whitelist = f'[^{whitelist}]'
    # Remove all non-allowed characters from string
    return sub(not_whitelist,'', text)



class APIServer(BaseHTTPRequestHandler):

    def do_GET(self):
        with open('static/api_instructions.txt', 'r') as file:
            self.usage = text2html(file.read())

        try:
            query = urlparse(self.path).query
            query = sanitize_input(query)
            query = query2dict(query)
        except:
            query = {}
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
            #self.wfile.write(bytes(self.usage, 'utf-8'))
        else:
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(bytes(json.dumps(response, ensure_ascii=False), 'utf-8'))


if __name__ == "__main__":  

    webServer = HTTPServer((hostName, serverPort), APIServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")