import httpx
import base64

class HTTPTunnel:
    """
    Covert HTTP Tunnel implementation.
    Encodes payload into X-Request-ID and X-Trace-ID headers.
    """

    @staticmethod
    def send(payload_bytes: bytes, target_url: str):
        # Base64 encode the payload
        encoded: str = base64.b64encode(payload_bytes).decode('utf-8')
        
        # Split payload if it's too long for a single header
        # X-Request-ID for part 1, X-Trace-ID for part 2
        mid = len(encoded) // 2
        headers = {
            "X-Request-ID": encoded[:mid],
            "X-Trace-ID": encoded[mid:]
        }
        
        with httpx.Client() as client:
            response = client.post(target_url, headers=headers, json={"ping": "pong"})
            return response

    @staticmethod
    def receive_from_headers(headers: dict):
        """
        Extracts and decodes payload from headers.
        """
        req_id = headers.get("X-Request-ID", "")
        trace_id = headers.get("X-Trace-ID", "")
        
        full_encoded = req_id + trace_id
        if not full_encoded:
            return b""
            
        try:
            return base64.b64decode(full_encoded)
        except Exception:
            return b""
