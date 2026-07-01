import os
import threading

from flask import Flask, jsonify, request

app = Flask(__name__)

_config_store: dict[str, str] = {}
_config_lock = threading.Lock()


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/version")
def version():
    return jsonify({"version": os.environ.get("VERSION", "1.0.0")})


@app.get("/env")
def env():
    return jsonify({"environment": os.environ.get("ENVIRONMENT", "")})


@app.post("/config")
def config_create():
    body = request.get_json(silent=True) or {}
    name = body.get("name")
    value = body.get("value")
    if name is None or value is None:
        return jsonify({"error": "name and value are required"}), 400
    with _config_lock:
        _config_store[name] = value
    return jsonify({"name": name, "value": value}), 201


@app.get("/config/<name>")
def config_get(name: str):
    with _config_lock:
        if name not in _config_store:
            return jsonify({"error": "not found"}), 404
        value = _config_store[name]
    return jsonify({"name": name, "value": value})


@app.delete("/config/<name>")
def config_delete(name: str):
    with _config_lock:
        if name not in _config_store:
            return jsonify({"error": "not found"}), 404
        del _config_store[name]
    return jsonify({"deleted": True})
