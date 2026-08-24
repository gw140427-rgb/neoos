from http.server import HTTPServer, BaseHTTPRequestHandler
import os

port = int(os.environ.get("PORT", 10000))


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"Ubuntu Docker Server Running!"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


server = HTTPServer(("0.0.0.0", port), Handler)

print("Server running on", port)

try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\nShutting down...")
finally:
    server.server_close()
