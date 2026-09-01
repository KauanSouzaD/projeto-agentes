# Quarto inteligente — agente adaptativo

O projeto usa Flask e preserva o padrão do sistema original: sensores atualizam
`estado_quarto`, o serviço decide e as ações são enviadas por HTTP às placas.
O modo padrão é `adaptativo`; configure `MODO_AGENTE` para integrar outros modos.

## PEAS

- **Performance:** conforto térmico e luminoso, segurança e baixo consumo, sem ar
  ligado com janela aberta e sem janela aberta durante chuva.
- **Ambiente:** quarto parcialmente observável, dinâmico e contínuo.
- **Atuadores:** janela, ar-condicionado, ventilador, lâmpada e umidificador.
- **Sensores:** chuva, luminosidade, temperatura, umidade e presenças interna/externa.

## Agentes

O código-base recebido contém um agente reativo no qual regras ligam o ar ou
movem a janela diretamente. Esta entrega implementa o agente adaptativo pedido.
O agente cognitivo descrito na especificação não faz parte desta entrega.

O agente adaptativo transforma cada leitura em um estado discreto composto por:
faixa de horário, temperatura, luminosidade, chuva, presenças e umidade. Ele
avalia as 11 ações declaradas em `adaptive_agent.py`. A pontuação é:

```text
utilidade total = preferência inicial + 1,5 × valor Q aprendido
```

As preferências iniciais expressam segurança, conforto e energia: chuva,
presença externa ou conflito janela/ar penalizam abrir a janela em 100 pontos;
ar custa 1,8 ponto; ventilação, iluminação e umidade recebem bônus somente
quando necessários. Todas as parcelas, o motivo e a escolha aparecem no
terminal e em `GET /interf/agente`.

Após uma avaliação, a tabela é atualizada por:

```text
Q(novo) = Q(anterior) + 0,4 × (recompensa - Q(anterior))
```

“Gostei/correto” vale `+1`; rejeição vale `-1`. Uma ação manual oposta à última
decisão (por exemplo, fechar logo após o agente abrir) também gera `-1`. A tabela
fica em `data/q_table.json` e é recarregada ao reiniciar.

## Execução

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
SIMULACAO=1 .venv/bin/python Servidor.py
```

Envie sensores reais ou simulados:

```bash
curl -X POST http://localhost:5050/interf/simular \
  -H 'Content-Type: application/json' \
  -d '{"temperatura":24,"umidade":50,"luminosidade":80,"chuva":false,"presencainterna":true}'
curl -X POST http://localhost:5050/interf/feedback \
  -H 'Content-Type: application/json' -d '{"avaliacao":"nao gostei"}'
curl -X POST http://localhost:5050/interf/acao/fechar_janela
```

Para a apresentação, simule luminosidade alta às 6h (ajustando o relógio do
sistema ou usando o teste), rejeite a abertura três vezes e repita o mesmo
estado. A lista de utilidades mostrará o Q negativo e outra ação será escolhida.
Execute os testes com `python3 -m unittest discover -s tests -v`.
