"""Integra sensores/atuadores existentes ao agente adaptativo."""

from datetime import datetime

import requests

from adaptive_agent import AdaptiveAgent
from config import SIMULACAO, estado_quarto, placas_registradas


agente_adaptativo = AdaptiveAgent()

ACTION_ENDPOINTS = {
    "abrir_janela": ("janela", "/abrir", {"janela_aberta": 1}),
    "fechar_janela": ("janela", "/fechar", {"janela_aberta": 0}),
    "ligar_ar": ("esp8266ar", "/ligar", {"ar_ligado": 1}),
    "desligar_ar": ("esp8266ar", "/desligar", {"ar_ligado": 0}),
    "ligar_ventilador": ("esp32c3vent", "/ventilador", {"ventilador": 1}),
    "desligar_ventilador": ("esp32c3vent", "/ventilador", {"ventilador": 0}),
    "ligar_umidificador": ("esp32c3vent", "/umidificador", {"umidificador": 1}),
    "desligar_umidificador": ("esp32c3vent", "/umidificador", {"umidificador": 0}),
    "ligar_lampada": ("esp32c3vent", "/lampada", {"lampada_ligada": 1}),
    "desligar_lampada": ("esp32c3vent", "/lampada", {"lampada_ligada": 0}),
}


def executar_acao(action):
    if action == "nao_fazer_nada":
        return {"executada": True, "simulacao": SIMULACAO}
    board, endpoint, changes = ACTION_ENDPOINTS[action]
    ip = placas_registradas.get(board)
    if not ip and not SIMULACAO:
        # A ausência temporária da placa não deve falsificar seu estado.
        print(f"Ação {action} não enviada: placa {board} não registrada.")
        return {"executada": False, "erro": f"Placa {board} não registrada"}
    if ip:
        response = requests.get(f"http://{ip}{endpoint}", timeout=5)
        response.raise_for_status()
    estado_quarto.update(changes)
    return {"executada": True, "simulacao": not bool(ip)}


def processar_sensores(dados, now=None):
    """Recebe leituras reais ou simuladas e executa uma decisão."""
    aliases = {
        "temperatura": "temperatura_atual", "umidade": "umidade_atual",
        "statusjanela": "janela_aberta", "presencainterna": "presenca_interna",
        "presencaexterna": "presenca_externa",
    }
    for name, value in dados.items():
        target = aliases.get(name, name)
        if target in estado_quarto:
            estado_quarto[target] = value
    for name in ("temperatura_atual", "umidade_atual", "luminosidade"):
        estado_quarto[name] = float(estado_quarto[name])
    for name in ("chuva", "presenca_interna", "presenca_externa", "janela_aberta"):
        value = estado_quarto[name]
        estado_quarto[name] = value if isinstance(value, bool) else str(value).lower() in ("1", "true", "sim")

    if estado_quarto.get("modo_agente") != "adaptativo":
        return None
    return agente_adaptativo.run(estado_quarto, executar_acao, now)


def registrar_feedback(reward):
    value = agente_adaptativo.feedback(reward)
    return {"recompensa": float(reward), "novo_valor_q": value,
            "ultima_decisao": agente_adaptativo.status()["ultima_decisao"]}


def feedback_por_correcao(manual_action, seconds=120):
    decision = agente_adaptativo.last_decision
    opposites = {"abrir_janela": "fechar_janela", "fechar_janela": "abrir_janela"}
    if not decision or opposites.get(decision.action) != manual_action:
        return None
    elapsed = datetime.now() - datetime.fromisoformat(decision.timestamp)
    return registrar_feedback(-1) if elapsed.total_seconds() <= seconds else None

