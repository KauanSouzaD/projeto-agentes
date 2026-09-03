"""Rotas web de controle, feedback e inspeção do aprendizado."""

from dataclasses import asdict

from flask import Blueprint, jsonify, request
import requests

import services
from config import estado_quarto


inter_bp = Blueprint("interf", __name__)


@inter_bp.get("/agente")
def painel_agente():
    return jsonify({"estado_atual": estado_quarto, **services.agente_adaptativo.status()})


@inter_bp.post("/feedback")
def feedback():
    data = request.get_json(silent=True) or request.form
    if "recompensa" in data:
        reward = data["recompensa"]
    else:
        reward = 1 if str(data.get("avaliacao", "")).lower() in ("gostei", "correto") else -1
    try:
        return jsonify(services.registrar_feedback(reward))
    except (TypeError, ValueError) as error:
        return jsonify({"erro": str(error)}), 400


@inter_bp.post("/acao/<action>")
def manual_action(action):
    if action not in services.ACTION_ENDPOINTS and action != "nao_fazer_nada":
        return jsonify({"erro": "Ação desconhecida"}), 404
    learned = services.feedback_por_correcao(action)
    try:
        result = services.executar_acao(action)
    except requests.exceptions.RequestException as error:
        return jsonify({"erro": str(error)}), 503
    return jsonify({"acao": action, "resultado": result,
                    "feedback_automatico": learned})


@inter_bp.post("/simular")
def simulate():
    data = request.get_json(silent=True) or {}
    decision = services.processar_sensores(data)
    return jsonify({"estado_atual": estado_quarto,
                    "decisao": asdict(decision) if decision else None})

@inter_bp.post("/responder")
def responder_pergunta():
    data = request.get_json(silent=True) or request.form
    resposta = data.get("resposta")
    if not resposta:
        return jsonify({"erro": "campo 'resposta' é obrigatório"}), 400
    try:
        decision = services.processar_resposta_pergunta(resposta)
    except (TypeError, ValueError) as error:
        return jsonify({"erro": str(error)}), 400
    return jsonify({"decisao": asdict(decision)})