"""Servidor Flask do quarto inteligente."""

from dataclasses import asdict

from flask import Flask, jsonify, request
import requests

import services
from config import estado_quarto, placas_registradas
from interface_bp import inter_bp


app = Flask(__name__)
app.register_blueprint(inter_bp, url_prefix="/interf")


@app.get("/")
def home():
    return jsonify({
        "projeto": "Quarto inteligente",
        "modo_agente": estado_quarto["modo_agente"],
        "rotas": ["POST /monitoramento", "GET /interf/agente",
                  "POST /interf/feedback", "POST /interf/simular"],
    })


@app.get("/placas")
def boards():
    return jsonify(placas_registradas)


@app.get("/meuip")
def register_ip():
    board, ip = request.args.get("placa"), request.args.get("ip")
    if not board or not ip:
        return jsonify({"erro": "placa e ip são obrigatórios"}), 400
    placas_registradas[board] = ip
    return jsonify({"status": "sucesso"})


@app.post("/monitoramento")
def monitoring():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"erro": "JSON de sensores obrigatório"}), 400
    try:
        decision = services.processar_sensores(data)
    except (TypeError, ValueError) as error:
        return jsonify({"erro": str(error)}), 400
    except requests.exceptions.RequestException as error:
        return jsonify({"erro": f"Falha no atuador: {error}"}), 503
    return jsonify({"message": "Dados processados", "decisao": asdict(decision) if decision else None})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
