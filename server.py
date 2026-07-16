from http.server import HTTPServer, BaseHTTPRequestHandler
import os

port = int(os.environ.get("PORT", 10000))

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Ubuntu Docker Server Running!")

server = HTTPServer(("0.0.0.0", port), Handler)

print("Server running on", port)
server.serve_forever()
