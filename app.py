import sys
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

# Use __import__ due to illegal characters for with with import.
mijnafvalwijzer_to_ical = __import__("mijnafvalwijzer-to-ical")

class MijnAfvalWijzerHTTPRequestHandler(BaseHTTPRequestHandler):
  def do_GET(self):
    url_params = urlparse(self.path)

    if url_params.path != "/":
      self.send_response(404)
      self.wfile.write(bytes("404 Not found.\n", "utf-8"))
      return

    query_params = parse_qs(url_params.query)
    postal_code = "".join(query_params.get("postal_code", None))
    housenumber = "".join(query_params.get("housenumber", None))
    waste_types = ",".join(query_params.get("waste_types", [])).split(",")

    errors = {}
    if postal_code is None:
      errors["postal_code"] = "Is missing."
    if housenumber is None:
      errors["housenumber"] = "Is missing."

    if len(errors.keys()) > 0:
      self.send_response(400)
      self.send_header("Content-type", "application/json")
      self.end_headers()

      data = {
        "success": False,
        "message": "Validation error(s).",
        "errors": errors
      }

      self.wfile.write(bytes(json.dumps(data), "utf-8"))
      self.wfile.write(bytes("\n", "utf-8"))

      return

    self.send_response(200)
    self.send_header("Content-type", "text/calendar")
    self.end_headers()

    ical = mijnafvalwijzer_to_ical.make_ical(postal_code, housenumber, waste_types)

    self.wfile.write(bytes(ical, "utf-8"))

if __name__ == "__main__":
  if len(sys.argv) < 2:
    print("Usage {0} <hostname> <port>".format(sys.argv[0]))
    exit(1)

  hostname = sys.argv[1]
  port = sys.argv[2]
  port = int(port)

  webServer = HTTPServer((hostname, port), MijnAfvalWijzerHTTPRequestHandler)
  print("Server started http://%s:%s" % (hostname, port))  #Server starts
  try:
    webServer.serve_forever()
  except KeyboardInterrupt:
    pass
  webServer.server_close()  #Executes when you hit a keyboard interrupt, closing the server
  print("Server stopped.")
