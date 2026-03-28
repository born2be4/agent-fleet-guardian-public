#!/usr/bin/env python3
"""n8n-bridge v2 — Fleet Message Hub
Central message bus for all fleet agents.

Endpoints:
  POST /message     — agent-to-agent messaging (resolves location automatically)
  POST /broadcast   — send to multiple agents / group
  POST /status      — query agent status
  POST /dispatch    — v1 compat (alias for /message)
  POST /relay       — SSH relay to remote macs
  GET  /health      — service health + agent count
  GET  /registry    — full agent registry
  GET  /logs        — recent message log (last N)
"""

import json
import subprocess
import sys
import os
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

PORT = 5679
MAX_LOG = 500  # keep last N messages in memory

# ──────────────── Agent Registry ────────────────
# location: local | rizz | semily | stas | dima
# type: managed (openclaw agent on local) | docker (container) | l1 (gateway on host)
# reach: how to send messages to this agent

AGENT_REGISTRY = {
    # ── LOCAL managed agents (sessions_send) ──
    "main":              {"mac": "local", "type": "managed", "session": "agent:main:main", "account": "default"},
    "hephaestus":        {"mac": "local", "type": "managed", "session": "agent:hephaestus:main", "account": "notion"},
    "cerberus":          {"mac": "local", "type": "managed", "session": "agent:cerberus:main", "account": "cerberus"},
    "iris":              {"mac": "local", "type": "managed", "session": "agent:iris:main", "account": "iris"},
    "athena":            {"mac": "local", "type": "managed", "session": "agent:athena:main", "account": "athena"},
    "prometheus":        {"mac": "local", "type": "managed", "session": "agent:prometheus:main", "account": "prometheus"},
    "hunter":            {"mac": "local", "type": "managed", "session": "agent:hunter:main", "account": "hunter"},

    # ── RIZZ L1 ──
    "sigma":             {"mac": "rizz", "type": "l1", "session": "agent:main:main"},

    # ── RIZZ Docker workers ──
    "rizz-marketing":           {"mac": "rizz", "type": "docker", "container": "worker-marketing"},
    "rizz-product-owner":       {"mac": "rizz", "type": "docker", "container": "worker-product-owner"},
    "rizz-sale":                {"mac": "rizz", "type": "docker", "container": "worker-sale"},
    "rizz-commercial-bloggers": {"mac": "rizz", "type": "docker", "container": "worker-commercial-bloggers"},
    "rizz-barter":              {"mac": "rizz", "type": "docker", "container": "worker-barter"},
    "rizz-archiver":            {"mac": "rizz", "type": "docker", "container": "worker-archiver"},
    "rizz-support":             {"mac": "rizz", "type": "docker", "container": "worker-support"},
    "rizz-analyst":             {"mac": "rizz", "type": "docker", "container": "worker-analyst"},
    "rizz-qa":                  {"mac": "rizz", "type": "docker", "container": "worker-qa"},
    "rizz-hr":                  {"mac": "rizz", "type": "docker", "container": "worker-hr"},
    "rizz-factory":             {"mac": "rizz", "type": "docker", "container": "worker-factory"},

    # ── SEMILY L1 ──
    "ceo-semily":        {"mac": "semily", "type": "l1", "session": "agent:main:main"},

    # ── SEMILY Docker workers ──
    "semily-knowledge-keeper":     {"mac": "semily", "type": "docker", "container": "worker-knowledge-keeper"},
    "semily-bizanalyst":           {"mac": "semily", "type": "docker", "container": "worker-bizanalyst"},
    "semily-bizanalyst-senior":    {"mac": "semily", "type": "docker", "container": "worker-bizanalyst-senior"},
    "semily-procurement":          {"mac": "semily", "type": "docker", "container": "worker-procurement"},
    "semily-merchandise":          {"mac": "semily", "type": "docker", "container": "worker-merchandise"},
    "semily-kolle":                {"mac": "semily", "type": "docker", "container": "worker-kolle"},
    "semily-itinfra":              {"mac": "semily", "type": "docker", "container": "worker-itinfra"},
    "semily-hr-nadya":             {"mac": "semily", "type": "docker", "container": "worker-hr-nadya"},
    "semily-dev-director":         {"mac": "semily", "type": "docker", "container": "worker-dev-director"},
    "semily-commercial-director":  {"mac": "semily", "type": "docker", "container": "worker-commercial-director"},
    "semily-cfo":                  {"mac": "semily", "type": "docker", "container": "worker-cfo"},
    "semily-anastasia":            {"mac": "semily", "type": "docker", "container": "worker-anastasia"},
    "semily-ads-growth":           {"mac": "semily", "type": "docker", "container": "worker-ads-growth"},

    # ── STAS L1 ──
    "stas-main":         {"mac": "stas", "type": "l1", "session": "agent:main:main"},

    # ── STAS Docker workers ──
    "stas-trust":        {"mac": "stas", "type": "docker", "container": "worker-trust"},
    "stas-data":         {"mac": "stas", "type": "docker", "container": "worker-data"},
    "stas-research":     {"mac": "stas", "type": "docker", "container": "worker-research"},
    "stas-qa":           {"mac": "stas", "type": "docker", "container": "worker-qa"},
    "stas-ops":          {"mac": "stas", "type": "docker", "container": "worker-ops"},
    "stas-cmo":          {"mac": "stas", "type": "docker", "container": "worker-cmo"},
    "stas-cfo":          {"mac": "stas", "type": "docker", "container": "worker-cfo"},
}

# SSH targets
SSH_MAP = {
    "rizz":   "rizz@192.168.10.134",
    "semily": "inhomacmini@192.168.10.213",
    "stas":   "stas@100.110.250.43",
    "dima":   "Дмитрий@100.96.52.102",
}

SSH_KEY = os.path.expanduser("~/.ssh/id_ed25519_noks")

# Groups for broadcast
GROUPS = {
    "local":     [k for k, v in AGENT_REGISTRY.items() if v["mac"] == "local"],
    "rizz":      [k for k, v in AGENT_REGISTRY.items() if v["mac"] == "rizz"],
    "semily":    [k for k, v in AGENT_REGISTRY.items() if v["mac"] == "semily"],
    "stas":      [k for k, v in AGENT_REGISTRY.items() if v["mac"] == "stas"],
    "all-l1":    [k for k, v in AGENT_REGISTRY.items() if v["type"] == "l1"],
    "all-docker":[k for k, v in AGENT_REGISTRY.items() if v["type"] == "docker"],
    "all":       list(AGENT_REGISTRY.keys()),
}

# ──────────────── Message Log ────────────────
message_log = []
log_lock = threading.Lock()

def log_message(sender, target, message, status, method=""):
    entry = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "sender": sender,
        "target": target,
        "message": message[:200],
        "status": status,
        "method": method,
    }
    with log_lock:
        message_log.append(entry)
        if len(message_log) > MAX_LOG:
            message_log.pop(0)
    return entry

# ──────────────── Delivery Methods ────────────────

def _run(cmd, timeout=30):
    """Run a subprocess, return (ok, stdout, stderr)"""
    try:
        env = {**os.environ, "PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:" + os.environ.get("PATH", "")}
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
        return r.returncode == 0, r.stdout.strip()[:500], r.stderr.strip()[:300]
    except subprocess.TimeoutExpired:
        return False, "", "timeout"
    except Exception as e:
        return False, "", str(e)

def deliver_local(agent_id, info, message, sender):
    """Deliver to local managed agent via openclaw cron add one-shot"""
    full_msg = f"[hub:{sender}] {message}"
    from datetime import datetime, timedelta, timezone
    fire_at = (datetime.now(timezone.utc) + timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ")

    if agent_id == "main":
        # main agent: systemEvent into main session
        cmd = [
            "openclaw", "cron", "add",
            "--name", "hub-msg",
            "--system-event", full_msg,
            "--at", fire_at,
            "--delete-after-run",
            "--json",
        ]
    else:
        # non-main agents: agentTurn into isolated session
        cmd = [
            "openclaw", "cron", "add",
            "--name", "hub-msg",
            "--agent", agent_id,
            "--message", full_msg,
            "--session", "isolated",
            "--at", fire_at,
            "--delete-after-run",
            "--no-deliver",
            "--json",
        ]
    ok, out, err = _run(cmd)
    return ok, "cron-local", out or err

def deliver_remote_l1(agent_id, info, message, sender):
    """Deliver to remote L1 via SSH + openclaw cron add one-shot"""
    mac = info["mac"]
    ssh_target = SSH_MAP.get(mac)
    if not ssh_target:
        return False, "ssh", f"no SSH target for mac {mac}"

    full_msg = f"[hub:{sender}] {message}"
    from datetime import datetime, timedelta, timezone
    fire_at = (datetime.now(timezone.utc) + timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ")

    cmd = (
        f'export PATH=/opt/homebrew/bin:/usr/local/bin:$PATH && '
        f'openclaw cron add '
        f'--name "hub-msg" '
        f'--system-event "{_shell_escape(full_msg)}" '
        f'--at "{fire_at}" '
        f'--delete-after-run '
        f'--json'
    )
    ok, out, err = _run([
        "ssh", "-i", SSH_KEY, "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=10", ssh_target, cmd
    ], timeout=30)
    return ok, "ssh-cron-l1", out or err

def deliver_remote_docker(agent_id, info, message, sender):
    """Deliver to remote Docker worker via SSH + docker exec + cron add one-shot"""
    mac = info["mac"]
    container = info["container"]
    ssh_target = SSH_MAP.get(mac)
    if not ssh_target:
        return False, "ssh", f"no SSH target for mac {mac}"

    full_msg = f"[hub:{sender}] {message}"
    # Calculate ISO time ~1 minute from now
    from datetime import datetime, timedelta, timezone
    fire_at = (datetime.now(timezone.utc) + timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ")

    cmd = (
        f'export PATH=/opt/homebrew/bin:/usr/local/bin:$PATH && '
        f'docker exec {container} openclaw cron add '
        f'--name "hub-msg" '
        f'--system-event "{_shell_escape(full_msg)}" '
        f'--at "{fire_at}" '
        f'--delete-after-run '
        f'--json'
    )
    ok, out, err = _run([
        "ssh", "-i", SSH_KEY, "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=10", ssh_target, cmd
    ], timeout=45)
    return ok, "ssh-docker-cron", out or err

def deliver(agent_id, message, sender="n8n"):
    """Route message to any agent in the fleet"""
    info = AGENT_REGISTRY.get(agent_id)
    if not info:
        return {"status": "error", "error": f"unknown agent: {agent_id}"}

    if info["mac"] == "local" and info["type"] == "managed":
        ok, method, detail = deliver_local(agent_id, info, message, sender)
    elif info["type"] == "l1":
        ok, method, detail = deliver_remote_l1(agent_id, info, message, sender)
    elif info["type"] == "docker":
        ok, method, detail = deliver_remote_docker(agent_id, info, message, sender)
    else:
        ok, method, detail = False, "unknown", f"no delivery method for type {info['type']}"

    status = "delivered" if ok else "failed"
    log_message(sender, agent_id, message, status, method)
    return {"status": status, "target": agent_id, "method": method, "detail": detail[:200]}

def _shell_escape(s):
    """Basic shell escape for embedding in double-quoted strings"""
    return s.replace('\\', '\\\\').replace('"', '\\"').replace('$', '\\$').replace('`', '\\`')

# ──────────────── Status Check ────────────────

def check_status(agent_id):
    """Check if an agent is reachable"""
    info = AGENT_REGISTRY.get(agent_id)
    if not info:
        return {"agent": agent_id, "status": "unknown", "error": "not in registry"}

    if info["mac"] == "local" and info["type"] == "managed":
        # Check via openclaw sessions list
        ok, out, _ = _run(["openclaw", "sessions", "list", "--agent", agent_id, "--limit", "1"])
        return {"agent": agent_id, "mac": "local", "status": "up" if ok else "unknown", "detail": out[:100]}

    mac = info["mac"]
    ssh_target = SSH_MAP.get(mac)
    if not ssh_target:
        return {"agent": agent_id, "mac": mac, "status": "unreachable", "error": "no SSH"}

    if info["type"] == "docker":
        cmd = f'export PATH=/opt/homebrew/bin:/usr/local/bin:$PATH && docker inspect -f "{{{{.State.Status}}}}" {info["container"]}'
    else:
        cmd = 'export PATH=/opt/homebrew/bin:/usr/local/bin:$PATH && openclaw status 2>&1 | head -5'

    ok, out, err = _run([
        "ssh", "-i", SSH_KEY, "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=10", ssh_target, cmd
    ], timeout=15)

    if ok:
        container_status = out.strip().lower()
        if info["type"] == "docker":
            is_up = container_status == "running"
        else:
            is_up = True
        return {"agent": agent_id, "mac": mac, "status": "up" if is_up else "down", "detail": out[:100]}
    return {"agent": agent_id, "mac": mac, "status": "unreachable", "detail": err[:100]}

# ──────────────── HTTP Handler ────────────────

class BridgeHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        routes = {
            "/message":   self.handle_message,
            "/dispatch":  self.handle_message,   # v1 compat
            "/broadcast": self.handle_broadcast,
            "/status":    self.handle_status,
            "/relay":     self.handle_relay,
        }

        handler = routes.get(self.path)
        if handler:
            result = handler(body)
        else:
            result = {"error": f"unknown path: {self.path}"}

        self._respond(result)

    def do_GET(self):
        if self.path == "/health":
            result = {
                "status": "ok",
                "version": 2,
                "agents": len(AGENT_REGISTRY),
                "macs": ["local", "rizz", "semily", "stas"],
                "uptime": int(time.time() - START_TIME),
            }
        elif self.path == "/registry":
            result = {k: {**v} for k, v in AGENT_REGISTRY.items()}
        elif self.path.startswith("/logs"):
            limit = 50
            try:
                if "?" in self.path:
                    params = dict(p.split("=") for p in self.path.split("?")[1].split("&"))
                    limit = int(params.get("limit", 50))
            except:
                pass
            with log_lock:
                result = {"logs": message_log[-limit:]}
        else:
            result = {"service": "n8n-bridge", "version": 2, "port": PORT}
        self._respond(result)

    def handle_message(self, body):
        target = body.get("target_agent") or body.get("target", "")
        message = body.get("message", "")
        sender = body.get("sender", "n8n")

        if not target or not message:
            return {"error": "missing target/target_agent and message"}

        return deliver(target, message, sender)

    def handle_broadcast(self, body):
        group = body.get("group", "")
        targets = body.get("targets", [])
        message = body.get("message", "")
        sender = body.get("sender", "n8n")

        if not message:
            return {"error": "missing message"}

        agent_list = []
        if group and group in GROUPS:
            agent_list = GROUPS[group]
        elif targets:
            agent_list = targets
        else:
            return {"error": "missing group or targets"}

        results = []
        for agent_id in agent_list:
            r = deliver(agent_id, message, sender)
            results.append(r)

        ok_count = sum(1 for r in results if r["status"] == "delivered")
        return {
            "status": "broadcast_done",
            "total": len(results),
            "delivered": ok_count,
            "failed": len(results) - ok_count,
            "results": results,
        }

    def handle_status(self, body):
        target = body.get("target_agent") or body.get("target", "")
        if target:
            return check_status(target)

        group = body.get("group", "")
        if group and group in GROUPS:
            results = [check_status(a) for a in GROUPS[group]]
            return {"group": group, "agents": results}

        return {"error": "missing target or group"}

    def handle_relay(self, body):
        """SSH relay to remote macs — v1 compat"""
        host = body.get("host", "")
        command = body.get("command", "")
        if not host or not command:
            return {"error": "missing host or command"}

        ssh_target = SSH_MAP.get(host, host)
        ok, out, err = _run([
            "ssh", "-i", SSH_KEY,
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=10",
            "-o", "ServerAliveInterval=3",
            "-o", "ServerAliveCountMax=2",
            ssh_target, command
        ], timeout=60)

        return {
            "status": "ok" if ok else "error",
            "host": host,
            "stdout": out[:2000],
            "stderr": err if not ok else "",
        }

    def _respond(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def log_message(self, format, *args):
        sys.stderr.write(f"[n8n-bridge] {args[0]} {args[1]} {args[2]}\n")


START_TIME = time.time()

if __name__ == "__main__":
    # Bind to all interfaces so remote agents can reach the hub
    server = HTTPServer(("0.0.0.0", PORT), BridgeHandler)
    print(f"n8n-bridge v2 listening on 127.0.0.1:{PORT} — {len(AGENT_REGISTRY)} agents registered", flush=True)
    server.serve_forever()
