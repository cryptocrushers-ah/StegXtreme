import socket

def get_local_ip():
    """
    Connects to 8.8.8.8 on UDP to discover outbound LAN interface.
    Does NOT send any data.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def get_shareable_url(port):
    """Returns full URL string like http://192.168.1.105:9000"""
    ip = get_local_ip()
    return f"http://{ip}:{port}"

def check_port_available(port):
    """Returns True if port is free, False if already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('0.0.0.0', port)) != 0
