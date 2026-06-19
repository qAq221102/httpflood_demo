import time
import threading
import collections
import psutil
import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# ── Shared State ──────────────────────────────────────────────
_lock = threading.Lock()

request_log     = collections.deque(maxlen=200)   # (timestamp, path, ip)
rps_window      = collections.deque()              # timestamps of recent requests
active_ips      = collections.Counter()            # ip → count
total_requests  = 0

# Flood thread control
flood_threads: list[threading.Thread] = []
flood_stop_event = threading.Event()
flood_active = False

TARGET_URL = "http://127.0.0.1:5000/demo"
NUM_THREADS = 40        # concurrent flood threads
THREAD_DELAY = 0.005    # seconds between each request per thread


# ── Request Tracking Middleware ───────────────────────────────
@app.before_request
def track_request():
    global total_requests
    ip = request.remote_addr
    path = request.path

    # Skip metrics endpoints to avoid inflating stats
    if path in ("/metrics", "/logs", "/status"):
        return

    now = time.time()
    with _lock:
        total_requests += 1
        request_log.appendleft({
            "ts": time.strftime("%H:%M:%S", time.localtime(now)),
            "path": path,
            "ip": ip,
            "method": request.method,
        })
        rps_window.append(now)
        active_ips[ip] += 1

        # Trim old timestamps outside 1-second window
        cutoff = now - 1.0
        while rps_window and rps_window[0] < cutoff:
            rps_window.popleft()


# ── Pages ─────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/demo")
def demo():
    return "OK", 200


# ── API Endpoints ─────────────────────────────────────────────
@app.route("/metrics")
def metrics():
    now = time.time()
    with _lock:
        # Trim rps_window
        cutoff = now - 1.0
        while rps_window and rps_window[0] < cutoff:
            rps_window.popleft()
        rps = len(rps_window)
        connections = sum(active_ips.values())
        top_ips = active_ips.most_common(10)

    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory().percent
    net = psutil.net_io_counters()

    return jsonify({
        "rps": rps,
        "total_requests": total_requests,
        "connections": connections,
        "top_ips": [{"ip": ip, "count": cnt} for ip, cnt in top_ips],
        "cpu": cpu,
        "ram": ram,
        "net_sent_mb": round(net.bytes_sent / 1024 / 1024, 2),
        "net_recv_mb": round(net.bytes_recv / 1024 / 1024, 2),
        "flood_active": flood_active,
    })


@app.route("/logs")
def logs():
    with _lock:
        recent = list(request_log)[:60]
    return jsonify(recent)


@app.route("/start", methods=["POST"])
def start_flood():
    global flood_threads, flood_active
    if flood_active:
        return jsonify({"status": "already running"})

    flood_stop_event.clear()
    flood_active = True

    def worker():
        sess = requests.Session()
        while not flood_stop_event.is_set():
            try:
                sess.get(TARGET_URL, timeout=2)
            except Exception:
                pass
            time.sleep(THREAD_DELAY)

    flood_threads = []
    for _ in range(NUM_THREADS):
        t = threading.Thread(target=worker, daemon=True)
        t.start()
        flood_threads.append(t)

    return jsonify({"status": "started", "threads": NUM_THREADS})


@app.route("/stop", methods=["POST"])
def stop_flood():
    global flood_active
    flood_stop_event.set()
    flood_active = False
    return jsonify({"status": "stopped"})


@app.route("/reset", methods=["POST"])
def reset_stats():
    global total_requests
    with _lock:
        request_log.clear()
        active_ips.clear()
        rps_window.clear()
        total_requests = 0
    return jsonify({"status": "reset"})


# ── Background CPU sampler (so interval=None is always fresh) ─
def cpu_sampler():
    while True:
        psutil.cpu_percent(interval=1)


threading.Thread(target=cpu_sampler, daemon=True).start()

if __name__ == "__main__":
    app.run(debug=False, threaded=True, port=5000)
