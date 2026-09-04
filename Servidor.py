"""Servidor Flask do quarto inteligente."""

import random
import threading
import time
from dataclasses import asdict
from functools import partial

from flask import Flask, jsonify, request
import requests

import services
from config import estado_quarto, placas_registradas, SIMULACAO
from interface_bp import inter_bp
from simulador import prever_estado, avaliar_resultado


app = Flask(__name__)
app.register_blueprint(inter_bp, url_prefix="/interf")


@app.get("/")
def home():
    return jsonify({
        "projeto": "Quarto inteligente",
        "modo_agente": estado_quarto["modo_agente"],
        "rotas": ["POST /monitoramento", "GET /interf/agente",
                  "POST /interf/feedback", "POST /interf/simular",
                  "POST /interf/responder"],
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


def treinar_em_segundo_plano():
    """Gera cenários aleatórios continuamente e deixa o agente treinar
    sozinho contra o simulador, sem nenhuma intervenção humana."""
    while True:
        temperatura_externa = random.uniform(10, 38)
        estado = {
            "temperatura_atual": random.uniform(18, 34),
            "umidade_atual": random.uniform(20, 80),
            "luminosidade": random.uniform(0, 100),
            "chuva": random.random() < 0.15,
            "presenca_interna": random.random() < 0.7,
            "presenca_externa": random.random() < 0.1,
            "janela_aberta": False, "ar_ligado": False, "ventilador": 0,
            "lampada_ligada": 0, "umidificador": 0,
        }
        prever = partial(prever_estado, temperatura_externa=temperatura_externa)
        services.agente_adaptativo.decidir_e_agir(
            estado, executor=lambda acao: None,
            simulador=(prever, avaliar_resultado),
        )
        time.sleep(0.05)

if SIMULACAO:
    threading.Thread(target=treinar_em_segundo_plano, daemon=True).start()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)