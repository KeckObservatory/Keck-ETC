from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
from calculator.ETC import exposure_time_calculator
from json import dumps as json


hostName = "0.0.0.0"
serverPort = 8080

# TODO -- initialize etc when beginning server, then reset it in between requests
def process_request(query):
    if len(query) == 0:
        return ''

    try:
        if isinstance(query['return'], list):
            return_vals = { x:[] for x in query['return'] }
        else:
            return_vals = { query['return'] : [] }
        del query['return']
        etc = exposure_time_calculator()  # Initialize etc
        etc.set_parameters(query)
        for key in return_vals.keys():
            return_vals[key] = vars(etc)[key].value.tolist()
        return return_vals, False
    except Exception as e:
        return f'An error occured while processing your request<br>{e}<br><br>', True

def text2html(text):
    text = text.replace(' ', '&nbsp;')
    text = text.replace('\t', '&nbsp'*4)
    text = text.replace('\n', '<br>')
    return text
           


class APIServer(BaseHTTPRequestHandler):

    def do_GET(self):
        with open('static/api_instructions.txt', 'r') as file:
            self.usage = text2html(file.read())

        try:
            query = urlparse(self.path).query
            query = dict(qc.split("=") for qc in query.split("&"))
            # Convert lists from string to list
            for key, val in query.items():
                if val.startswith('[') and val.endswith(']'):
                    query[key] = [x.strip() for x in val[1:-1].split(',')]
        except:
            query = {}
        response, error = process_request(query)
        if error or len(response)==0:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(bytes(response, 'utf-8'))
            self.wfile.write(bytes(self.usage, 'utf-8'))
        else:
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(bytes(json(response, ensure_ascii=False), 'utf-8'))


if __name__ == "__main__":        
    webServer = HTTPServer((hostName, serverPort), APIServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")