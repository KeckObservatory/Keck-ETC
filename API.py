from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
from ETC import exposure_time_calculator


hostName = "localhost"
serverPort = 8080

# TODO -- initialize etc when beginning server, then reset it in between requests
def process_request(query):
    try:
        if isinstance(query['return'], list):
            return_vals = { x:[] for x in query['return'] }
        else:
            return_vals = { query['return'] : [] }
        del query['return']
        
        etc = exposure_time_calculator()  # Initialize etc
        etc.set_parameters(query)
        for key in return_vals.keys():
            return_vals['key'] = vars(etc)[key]
        return return_vals, False
    except:
        return '''  <html><body>
                        <p>An error occured while processing your request.</p>
                        <p>API usage:</p>
                        <p>Detailed instructions to come...</p>
                    </body></html>''', True
           


class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        query = urlparse(self.path).query
        query = {qc.split("=") for qc in query.split("&")}
        response, error = process_request(query)
        if error:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(bytes(response, 'utf-8'))
        elif len(response)==0:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(bytes('Usage: ...', 'utf-8'))
        else:
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(bytes(response, 'utf-8'))


if __name__ == "__main__":        
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")