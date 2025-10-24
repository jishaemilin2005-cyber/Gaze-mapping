#!/usr/bin/env python3
"""
Simple HTTP server for eye tracking application.
Binds to 0.0.0.0 and uses PORT environment variable.
"""
import os
import http.server
import socketserver
import sys

PORT = int(os.getenv('PORT', 8000))
HOST = '0.0.0.0'

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.send_header('Expires', '0')
        super().end_headers()

def run_server():
    Handler = MyHTTPRequestHandler

    with socketserver.TCPServer((HOST, PORT), Handler) as httpd:
        # Get workspace ID from environment (Bolt sets this)
        workspace_id = os.getenv('BOLT_WORKSPACE_ID', 'localhost')

        print("\n" + "=" * 60)
        print("🌐 Eye Tracking System Server")
        print("=" * 60)
        print(f"\n✅ Server running on {HOST}:{PORT}")

        if workspace_id != 'localhost':
            external_url = f"https://{workspace_id}-{PORT}.bolt.run"
            print(f"\n🔗 Open the app at: {external_url}")
            print(f"\n📄 Available pages:")
            print(f"   • Home:    {external_url}/index.html")
            print(f"   • Study:   {external_url}/study.html")
            print(f"   • Demo:    {external_url}/demo_tracker.html")
            print(f"   • Results: {external_url}/results.html")
        else:
            print(f"\n🔗 Local URL: http://localhost:{PORT}")
            print(f"\n📄 Available pages:")
            print(f"   • Home:    http://localhost:{PORT}/index.html")
            print(f"   • Study:   http://localhost:{PORT}/study.html")
            print(f"   • Demo:    http://localhost:{PORT}/demo_tracker.html")
            print(f"   • Results: http://localhost:{PORT}/results.html")

        print("\n" + "=" * 60)
        print("Press Ctrl+C to stop the server")
        print("=" * 60 + "\n")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n⚠️  Server stopped")
            sys.exit(0)

if __name__ == '__main__':
    run_server()
