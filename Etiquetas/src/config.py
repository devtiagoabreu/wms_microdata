import socket

def get_local_ip():
    """Obtém o IP local da máquina"""
    try:
        # Cria um socket temporário para descobrir o IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

# Configurações
HOST = get_local_ip()  # IP automático da máquina
PORT = 5000
DEBUG = True
THREADED = True  # Permite múltiplas conexões

# URL de acesso
APP_URL = f"http://{HOST}:{PORT}"
NETWORK_URL = f"http://{HOST}:{PORT}"  # Para acesso na rede

print(f"🌐 IP Local: {HOST}")
print(f"🔌 Porta: {PORT}")
print(f"🚀 URL Local: {APP_URL}")
print(f"🌍 URL da Rede: {NETWORK_URL}")