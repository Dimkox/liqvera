import json
import os
import socket
import subprocess
import sys
import threading

binary = sys.argv[1]


def check(name, path, reject=False, proxy=False):
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    server.settimeout(0.4)
    port = server.getsockname()[1]
    received = []

    def serve():
        try:
            conn, _ = server.accept()
            conn.settimeout(2)
            received.append(conn.recv(4096).decode("ascii"))
            conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\nConnection: close\r\n\r\n")
            conn.close()
        except socket.timeout:
            pass

    thread = threading.Thread(target=serve)
    thread.start()
    env = {k: v for k, v in os.environ.items() if "proxy" not in k.lower()}
    url = f"http://127.0.0.1:{port}{path}"
    if proxy:
        url = "http://example.invalid\r\nX-Liqvera-Audit: injected/audit"
        env["http_proxy"] = f"http://127.0.0.1:{port}"
    proc = subprocess.run(
        [binary, "wget", "-q", "-O", "/dev/null", url], env=env, capture_output=True, timeout=3
    )
    thread.join()
    server.close()
    outcome = {
        "case": name,
        "returncode": proc.returncode,
        "connected": bool(received),
        "injected_header": any("\r\nX-Liqvera-Audit: injected" in raw for raw in received),
        "passed": (
            proc.returncode == 1
            and b"Unencoded control character found in the URL!" in proc.stderr
            and not received
        )
        if reject
        else (proc.returncode == 0 and bool(received)),
    }
    if received:
        outcome["request_line"] = received[0].split("\r\n")[0]
    return outcome


rows = [
    check("ordinary", "/audit"),
    check("percent_encoded", "/audit%20encoded"),
    check("path_crlf", "/audit\r\nX-Liqvera-Audit: injected", True),
    check("path_cr", "/audit\rcontrol", True),
    check("path_lf", "/audit\ncontrol", True),
    check("path_tab", "/audit\tcontrol", True),
    check("path_space", "/audit space", True),
    check("proxy_host_crlf", "", True, True),
]
print(
    json.dumps(
        {"binary": binary, "all_passed": all(row["passed"] for row in rows), "cases": rows},
        indent=2,
    )
)
sys.exit(0 if all(row["passed"] for row in rows) else 1)
