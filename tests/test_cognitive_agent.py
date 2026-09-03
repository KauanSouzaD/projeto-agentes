import unittest

from cognitive_agent import CognitiveAgent


def room(**changes):
    state = {
        "temperatura_atual": 29, "umidade_atual": 50, "luminosidade": 70,
        "chuva": False, "presenca_interna": True, "presenca_externa": False,
        "janela_aberta": False, "ar_ligado": False,
    }
    state.update(changes)
    return state


class CognitiveAgentTests(unittest.TestCase):
    def test_compares_options_for_hot_room(self):
        decision = CognitiveAgent().decide(room())
        self.assertEqual(len(decision.evaluated_options), 5)
        self.assertEqual(decision.plan, "ar_condicionado")

    def test_never_opens_window_during_rain(self):
        decision = CognitiveAgent().decide(room(chuva=True))
        self.assertNotIn("abrir_janela", decision.actions)
        opening = next(x for x in decision.evaluated_options if x["opcao"] == "abrir_janela")
        self.assertLess(opening["utilidade"], -90)

    def test_ac_plan_closes_window_first(self):
        decision = CognitiveAgent().decide(room(temperatura_atual=34, janela_aberta=True))
        if decision.plan == "ar_condicionado":
            self.assertEqual(decision.actions, ["fechar_janela", "ligar_ar"])


if __name__ == "__main__":
    unittest.main()
