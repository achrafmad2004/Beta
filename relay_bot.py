import socket
import threading
import time

# === CONFIG ===
SERVER_HOST = "161.35.252.15"
SERVER_PORT = 6858
RELAY_PORT = 20002
USERNAME = "Achraf~1"
VERSION = "0.2.11-MULTIPLAYER"

# === Keep-alive thread ===
def keep_alive(sock):
    while True:
        try:
            sock.sendall(b"action:keepAliveAck\n")
            print("[KA] Sent keepAliveAck")
            time.sleep(4)
        except Exception as e:
            print(f"[X] Keep-alive error: {e}")
            break

# === Forwarding proxy data ===
def handle_proxy_connection(proxy_sock, server_sock):
    def forward(src, dst, label):
        try:
            while True:
                data = src.recv(4096)
                if not data:
                    break
                print(f"[{label}] {data!r}")
                dst.sendall(data)
        except Exception as e:
            print(f"[X] Forwarding error ({label}): {e}")
        finally:
            print(f"[~] Closing {label}")

    threading.Thread(target=forward, args=(proxy_sock, server_sock, "Proxy → Server"), daemon=True).start()
    threading.Thread(target=forward, args=(server_sock, proxy_sock, "Server → Proxy"), daemon=True).start()

# === Main relay logic ===
def main():
    print("[BOOT] Relay starting...")

    # === Step 1: Connect to Balatro server ===
    try:
        print(f"[CONNECT] Connecting to Balatro server at {SERVER_HOST}:{SERVER_PORT}...")
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.connect((SERVER_HOST, SERVER_PORT))
        print("[✓] Connected to Balatro server.")

        # === Step 2: Perform authentication handshake ===
        encrypt_id = generate_encrypt_id()
        mod_hash = build_mod_hash(encrypt_id)

        server_sock.sendall(f"action:username,username:{USERNAME},modHash:\n".encode())
        server_sock.sendall(f"action:version,version:{VERSION}\n".encode())
        server_sock.sendall(f"action:username,username:{USERNAME},modHash:{mod_hash}\n".encode())
        print("[→] Sent authentication handshake.")

        # Start keep-alive ping
        threading.Thread(target=keep_alive, args=(server_sock,), daemon=True).start()

    except Exception as e:
        print(f"[X] Failed to connect to Balatro server: {e}")
        return

    # === Step 3: Accept proxy connections ===
    try:
        relay_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        relay_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        relay_sock.bind(("0.0.0.0", RELAY_PORT))
        relay_sock.listen(5)
        print(f"[LISTENING] Relay is ready on port {RELAY_PORT}. Waiting for proxy...")

        while True:
            proxy_sock, addr = relay_sock.accept()
            print(f"[+] Proxy connected from {addr}")
            threading.Thread(target=handle_proxy_connection, args=(proxy_sock, server_sock), daemon=True).start()

    except Exception as e:
        print(f"[X] Relay error: {e}")

if __name__ == "__main__":
    main()
