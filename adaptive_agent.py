"""Agente adaptativo didático baseado em uma tabela Q persistente."""

from __future__ import annotations

import json
import random
import threading
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable


ACTIONS = (
    "abrir_janela", "fechar_janela", "ligar_ar", "desligar_ar",
    "ligar_ventilador", "desligar_ventilador", "ligar_lampada",
    "desligar_lampada", "ligar_umidificador", "desligar_umidificador",
    "nao_fazer_nada",
)

AMBIGUITY_THRESHOLD = 0.5  # diferença mínima entre a 1ª e a 2ª ação pra considerar "certeza"

ACTION_LABELS = {
    "abrir_janela": "abrir a janela",
    "fechar_janela": "fechar a janela",
    "ligar_ar": "ligar o ar-condicionado",
    "desligar_ar": "desligar o ar-condicionado",
    "ligar_ventilador": "ligar o ventilador",
    "desligar_ventilador": "desligar o ventilador",
    "ligar_lampada": "ligar a lâmpada",
    "desligar_lampada": "desligar a lâmpada",
    "ligar_umidificador": "ligar o umidificador",
    "desligar_umidificador": "desligar o umidificador",
    "nao_fazer_nada": "não fazer nada",
}


@dataclass
class Decision:
    state_key: str
    state: dict
    action: str
    base_score: float
    learned_value: float
    total_score: float
    reason: str
    evaluated_actions: list[dict]
    timestamp: str
    reward: float | None = None
    pergunta: str | None = None
    candidatos_pergunta: list[str] | None = None


class AdaptiveAgent:
    def __init__(self, table_path="data/q_table.json", alpha=0.4, epsilon=0.0):
        self.path = Path(table_path)
        self.alpha = alpha
        self.epsilon = epsilon
        self._lock = threading.RLock()
        self.q_table = self._load()
        self.last_decision: Decision | None = None

    def _load(self):
        try:
            with self.path.open(encoding="utf-8") as stream:
                data = json.load(stream)
            return data if isinstance(data, dict) else {}
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {}

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(self.q_table, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        temporary.replace(self.path)

    @staticmethod
    def encode_state(sensor_state, now=None):
        now = now or datetime.now()
        hour = now.hour
        if hour < 6:
            time_band = "madrugada"
        elif hour < 7:
            time_band = "06h"
        elif hour < 12:
            time_band = "manha"
        elif hour < 18:
            time_band = "tarde"
        else:
            time_band = "noite"
        temperature = float(sensor_state.get("temperatura_atual", 24))
        humidity = float(sensor_state.get("umidade_atual", 50))
        luminosity = float(sensor_state.get("luminosidade", 0))
        compact = {
            "horario": time_band,
            "temperatura": "fria" if temperature < 22 else "confortavel" if temperature <= 26 else "quente",
            "luminosidade": "alta" if luminosity >= 60 else "baixa",
            "chuva": bool(sensor_state.get("chuva", False)),
            "presenca_interna": bool(sensor_state.get("presenca_interna", False)),
            "presenca_externa": bool(sensor_state.get("presenca_externa", False)),
            "umidade": "baixa" if humidity < 40 else "adequada" if humidity <= 65 else "alta",
        }
        key = "|".join(f"{name}={value}" for name, value in compact.items())
        return key, compact

    @staticmethod
    def _base_score(action, state):
        """Preferências iniciais; o feedback aprendido é somado a elas."""
        temp = float(state.get("temperatura_atual", 24))
        humidity = float(state.get("umidade_atual", 50))
        light = float(state.get("luminosidade", 0))
        rain = bool(state.get("chuva"))
        outside = bool(state.get("presenca_externa"))
        inside = bool(state.get("presenca_interna"))
        window = bool(state.get("janela_aberta"))
        ac = bool(state.get("ar_ligado"))
        fan = bool(state.get("ventilador"))
        lamp = bool(state.get("lampada_ligada"))
        humidifier = bool(state.get("umidificador"))
        score, reasons = 0.0, []

        if action == "abrir_janela":
            score += 1.3 if light >= 60 else -0.2
            reasons.append("aproveita luz/ventilação natural")
            if temp > 26:
                score += 0.7
            if rain:
                score -= 100
                reasons.append("proibida durante chuva")
            if outside:
                score -= 100
                reasons.append("risco de segurança externo")
            if ac:
                score -= 100
                reasons.append("conflito com ar-condicionado")
            if window:
                score -= 1
        elif action == "fechar_janela":
            score += 4 if rain or outside else (-0.3 if not window else 0.2)
            reasons.append("protege contra chuva/presença externa" if rain or outside else "mantém a janela fechada")
        elif action == "ligar_ar":
            score += max(0, temp - 24) * 0.8 - 1.8
            score -= 100 if window else 0
            reasons.append("resfria com maior consumo")
        elif action == "desligar_ar":
            score += 1.2 if temp <= 25 and ac else -0.2
            reasons.append("economiza energia")
        elif action == "ligar_ventilador":
            score += 1.2 if temp > 26 and inside else -0.4
            score -= 1 if fan else 0
            reasons.append("conforto com baixo consumo")
        elif action == "desligar_ventilador":
            score += (0.6 if temp <= 25 or not inside else -0.3) if fan else -0.5
            reasons.append("economiza energia")
        elif action == "ligar_lampada":
            score += 1 if light < 35 and inside else -1
            score -= 1 if lamp else 0
            reasons.append("corrige iluminação baixa")
        elif action == "desligar_lampada":
            score += (0.8 if light >= 60 or not inside else -0.3) if lamp else -0.5
            reasons.append("aproveita luz natural/economiza")
        elif action == "ligar_umidificador":
            score += 1 if humidity < 40 and inside else -0.8
            score -= 1 if humidifier else 0
            reasons.append("corrige umidade baixa")
        elif action == "desligar_umidificador":
            score += (0.7 if humidity >= 45 or not inside else -0.3) if humidifier else -0.5
            reasons.append("evita consumo desnecessário")
        else:
            score = 0.25
            reasons.append("estado não exige mudança")
        return round(score, 3), "; ".join(reasons)

    def decide(self, sensor_state, now=None):
        key, compact = self.encode_state(sensor_state, now)
        values = self.q_table.get(key, {})
        evaluated = []
        for action in ACTIONS:
            base, reason = self._base_score(action, sensor_state)
            learned = float(values.get(action, 0.0))
            evaluated.append({"acao": action, "utilidade_base": base,
                              "valor_aprendido": round(learned, 3),
                              "utilidade_total": round(base + 1.5 * learned, 3),
                              "motivo": reason})

        pergunta = None
        candidatos = None
        explorou = random.random() < self.epsilon
        if explorou:
            selected = random.choice(evaluated)
            selected = {**selected, "motivo": selected["motivo"] + "; exploração"}
        else:
            ranking = sorted(evaluated, key=lambda item: item["utilidade_total"], reverse=True)
            selected = ranking[0]
            if len(ranking) > 1:
                diferenca = ranking[0]["utilidade_total"] - ranking[1]["utilidade_total"]
                if diferenca < AMBIGUITY_THRESHOLD and ranking[0]["acao"] != ranking[1]["acao"]:
                    candidatos = [ranking[0]["acao"], ranking[1]["acao"]]
                    pergunta = (
                        f"Não tenho certeza: devo {ACTION_LABELS[candidatos[0]]} "
                        f"ou {ACTION_LABELS[candidatos[1]]}?"
                    )

        decision = Decision(
            key, compact, selected["acao"], selected["utilidade_base"],
            selected["valor_aprendido"], selected["utilidade_total"],
            selected["motivo"], evaluated,
            (now or datetime.now()).isoformat(timespec="seconds"),
            pergunta=pergunta, candidatos_pergunta=candidatos,
        )
        self.last_decision = decision
        self._print_decision(decision)
        return decision

    def run(self, sensor_state, executor: Callable[[str], object], now=None):
        decision = self.decide(sensor_state, now)
        if decision.pergunta:
            return decision
        executor(decision.action)
        return decision

    def decidir_e_agir(self, sensor_state, executor, simulador=None, now=None):
        """Decide e executa sempre, sem depender de resposta humana.
        Se estiver em dúvida, simula o resultado de cada candidata e
        escolhe/aprende sozinho antes de agir."""
        decision = self.decide(sensor_state, now)

        if decision.pergunta and simulador:
            prever_estado, avaliar_resultado = simulador
            notas = {}
            for acao in decision.candidatos_pergunta:
                previsto = prever_estado(sensor_state, acao)
                notas[acao] = avaliar_resultado(previsto)
            escolhida = max(notas, key=notas.get)

            with self._lock:
                state_values = self.q_table.setdefault(decision.state_key, {})
                for acao, nota in notas.items():
                    alvo = 1.0 if acao == escolhida else -0.3
                    old = float(state_values.get(acao, 0.0))
                    state_values[acao] = round(old + self.alpha * (alvo - old), 6)
                self._save()

            decision.action = escolhida
            decision.reason += f"; resolvido por simulação (notas={notas})"
            decision.pergunta = None

        executor(decision.action)
        return decision

    def feedback(self, reward):
        if not self.last_decision:
            raise ValueError("Ainda não existe uma decisão para avaliar.")
        reward = float(reward)
        decision = self.last_decision
        with self._lock:
            state_values = self.q_table.setdefault(decision.state_key, {})
            old = float(state_values.get(decision.action, 0.0))
            state_values[decision.action] = round(old + self.alpha * (reward - old), 6)
            decision.reward = reward
            decision.learned_value = state_values[decision.action]
            self._save()
        return state_values[decision.action]

    def aprender_com_resultado_real(self, estado_antes, decisao, estado_depois, avaliar_resultado):
        """Compara o estado real antes/depois de uma ação e gera uma
        recompensa automática, sem nenhuma intervenção humana."""
        nota_antes = avaliar_resultado(estado_antes)
        nota_depois = avaliar_resultado(estado_depois)
        reward = round(nota_depois - nota_antes, 3)

        with self._lock:
            state_values = self.q_table.setdefault(decisao.state_key, {})
            old = float(state_values.get(decisao.action, 0.0))
            state_values[decisao.action] = round(old + self.alpha * (reward - old), 6)
            self._save()
        return reward

    def responder_pergunta(self, resposta: str, executor):
        decision = self.last_decision
        if not decision or not decision.pergunta:
            raise ValueError("Não há pergunta pendente para responder.")

        resposta_normalizada = resposta.strip().lower()
        escolhida = None
        for acao in decision.candidatos_pergunta:
            if ACTION_LABELS[acao].lower() in resposta_normalizada or acao in resposta_normalizada:
                escolhida = acao
                break
        if escolhida is None:
            # fallback: mantém a que já tinha maior pontuação
            escolhida = decision.candidatos_pergunta[0]

        executor(escolhida)

        # aprendizado: reforça a ação escolhida, penaliza levemente a alternativa
        with self._lock:
            state_values = self.q_table.setdefault(decision.state_key, {})
            for acao in decision.candidatos_pergunta:
                alvo = 1.0 if acao == escolhida else -0.3
                old = float(state_values.get(acao, 0.0))
                state_values[acao] = round(old + self.alpha * (alvo - old), 6)
            self._save()

        decision.action = escolhida
        decision.pergunta = None
        decision.reward = 1.0
        return decision

    def status(self):
        return {
            "ultima_decisao": asdict(self.last_decision) if self.last_decision else None,
            "estados_aprendidos": len(self.q_table),
            "tabela_q": self.q_table,
        }


    @staticmethod
    def _print_decision(decision):
        print("\n=== AGENTE ADAPTATIVO ===")
        print("Estado:", decision.state)
        for item in decision.evaluated_actions:
            print(f"- {item['acao']}: {item['utilidade_total']:.3f} "
                  f"(base={item['utilidade_base']:.3f}, Q={item['valor_aprendido']:.3f})")
        print(f"Escolhida: {decision.action} — {decision.reason}")
