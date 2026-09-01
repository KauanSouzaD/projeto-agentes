Analise todos os arquivos existentes deste projeto antes de fazer qualquer alteração.

Este projeto é uma atividade da disciplina de Inteligência Artificial. Já existe um **Agente Reativo Simples** funcionando para automação de um quarto inteligente. Quero que você utilize a estrutura, tecnologias, sensores, atuadores, nomes de arquivos, padrões e código já existentes como base, sem recriar o projeto do zero.

O PEAS definido para o sistema é:

P — Performance:
- Maximizar o conforto térmico.
- Maximizar a iluminação adequada.
- Maximizar a segurança.
- Minimizar o consumo de energia.
- Evitar situações como ar-condicionado ligado com janela aberta.
- Fechar a janela quando houver chuva.
- Considerar segurança relacionada à presença externa.

E — Ambiente:
- Quarto inteligente.
- Parcialmente observável.
- Dinâmico.
- Contínuo.

A — Atuadores:
- Motor da janela.
- Relé do ar-condicionado.
- Relé do ventilador.
- Relé do umidificador.
- Relé da lâmpada.

S — Sensores:
- Sensor de chuva.
- Sensor de luminosidade.
- Sensor de temperatura.
- Sensor de umidade DHT.
- Sensor de presença interna PIR.
- Sensor de presença externa utilizando motor de 180 graus + sensor AJ-SR04M.

O agente reativo simples já existente funciona basicamente por regras diretas, por exemplo:
- Choveu → fechar janela.
- Está quente → ligar ar-condicionado.

A atividade agora exige criar mais dois agentes:

1. AGENTE COGNITIVO / BASEADO EM OBJETIVO E UTILIDADE

Implemente um novo agente que tome decisões avaliando alternativas antes de executar uma ação.

Objetivo principal de conforto térmico:
- Tentar manter a temperatura do quarto próxima de 24 °C.

Exemplo esperado:
Se a temperatura estiver em 29 °C, o agente não deve simplesmente ligar o ar-condicionado.

Ele deve analisar opções como:
- Ligar o ar-condicionado.
- Abrir a janela.
- Abrir a janela e ligar o ventilador.
- Apenas ligar o ventilador.
- Não fazer nada, dependendo das condições.

Cada opção deve possuir uma função de utilidade.

A utilidade deve considerar pelo menos:
- Distância da temperatura desejada de 24 °C.
- Consumo de energia.
- Chuva.
- Estado da janela.
- Presença.
- Luminosidade.
- Umidade.
- Segurança.
- Conflitos entre dispositivos.

Exemplos:
- Ar-condicionado resfria mais, porém gasta mais energia.
- Ventilador consome menos energia.
- Abrir a janela pode ser uma boa estratégia de baixo consumo, mas deve ser proibido ou fortemente penalizado se estiver chovendo.
- Ar-condicionado ligado com janela aberta deve receber uma penalidade muito alta.
- Ações perigosas ou incoerentes devem possuir utilidade muito baixa.

Crie uma estrutura clara semelhante a:

Sensores
→ leitura do estado atual
→ geração das ações possíveis
→ cálculo da utilidade de cada ação
→ escolha da ação com maior utilidade
→ execução nos atuadores.

Quero que o código deixe evidente durante a apresentação acadêmica:
- qual é o estado atual;
- quais ações foram avaliadas;
- qual foi a utilidade calculada para cada ação;
- qual ação foi escolhida;
- por que ela foi escolhida.

Sempre que possível, mostre essas informações no terminal, log ou interface existente.

Não utilize IA generativa ou APIs externas para tomar as decisões. A inteligência desse agente deve estar implementada explicitamente através da função de utilidade.

2. AGENTE ADAPTATIVO / COM APRENDIZAGEM

Também implemente um segundo agente utilizando a mesma estrutura do projeto.

Esse agente deve aprender com o feedback do usuário.

Cenário principal da atividade:

Imagine que o sistema percebe aumento da luminosidade às 6h da manhã e começa a abrir automaticamente a janela.

Porém, o usuário prefere dormir até as 7h.

Quando o agente abrir a janela às 6h, o usuário utilizará a interface existente ou uma nova interface web simples para mandar fechar a janela ou informar que aquela decisão foi ruim.

Essa correção deve gerar uma recompensa negativa.

Exemplo:

Agente:
06:00 → luminosidade aumentou → abrir janela.

Usuário:
fecha a janela / informa que não gostou.

Sistema:
recompensa = -1.

O agente deve registrar essa experiência e ajustar seus valores internos.

Após várias correções semelhantes, o agente deve aprender algo equivalente a:

"Abrir a janela às 6h neste contexto possui baixa utilidade."

Consequentemente, depois de algumas interações, ele deve deixar de abrir a janela às 6h e passar a preferir abrir depois das 7h ou considerar outras informações, como presença interna.

Implemente um mecanismo simples e didático de aprendizagem por reforço.

Não precisa utilizar bibliotecas complexas de Machine Learning.

Pode ser implementado com uma tabela de valores ou Q-Learning simplificado.

Considere algo semelhante a:

Estado:
- faixa de horário;
- temperatura;
- luminosidade;
- chuva;
- presença interna;
- presença externa;
- umidade.

Ações:
- abrir janela;
- fechar janela;
- ligar/desligar ar-condicionado;
- ligar/desligar ventilador;
- ligar/desligar lâmpada;
- ligar/desligar umidificador;
- não fazer nada.

Recompensas:
- +1 quando o usuário aprovar a decisão;
- -1 quando o usuário corrigir/rejeitar a decisão;
- opcionalmente pequenas recompensas automáticas por economia de energia e conforto.

O aprendizado precisa persistir entre execuções.

Portanto, armazene os valores aprendidos em uma solução simples compatível com o projeto atual, por exemplo:
- arquivo JSON;
- banco já existente;
- armazenamento equivalente já utilizado pelo projeto.

Ao iniciar novamente o sistema, o agente deve carregar o aprendizado anterior.

INTERFACE DE FEEDBACK

Analise primeiro se já existe uma interface web no projeto.

Se existir, aproveite-a.

Adicione controles simples relacionados à última decisão do agente, como:
- "Gostei";
- "Não gostei";
ou
- "Correto";
- "Corrigir".

Também deve ser possível realizar uma ação manual, como fechar a janela.

Se o usuário corrigir manualmente imediatamente após uma decisão automática do agente, essa intervenção pode ser interpretada como feedback negativo para aquela decisão.

Mostre na interface, se possível:
- estado atual;
- última decisão;
- motivo;
- utilidade;
- recompensa recebida;
- aprendizado atual.

ORGANIZAÇÃO

Antes de alterar código:

1. Examine toda a estrutura do projeto.
2. Identifique linguagem, framework e arquitetura atual.
3. Identifique como o agente reativo simples está implementado.
4. Identifique como os sensores são lidos.
5. Identifique como os atuadores são acionados.
6. Identifique se existe frontend/interface web.
7. Preserve tudo que já funciona.

Não substitua sensores reais por simulações se eles já estiverem implementados.

Entretanto, como este é um projeto acadêmico, se algum hardware não estiver conectado durante os testes, crie uma forma de simular os valores dos sensores sem remover o suporte ao hardware real.

Organize os três agentes de forma que seja fácil alternar entre:

- reativo simples;
- cognitivo;
- adaptativo.

Por exemplo, por configuração, enum, variável ou opção da interface.

Evite duplicação de código. Reutilize leitura de sensores e controle dos atuadores.

DOCUMENTAÇÃO

Depois de implementar, crie ou atualize o README.md explicando:

1. O PEAS do sistema.
2. Como funciona o agente reativo simples.
3. Como funciona o agente cognitivo.
4. Como funciona a função de utilidade.
5. Quais valores/pesos foram utilizados.
6. Como funciona o agente adaptativo.
7. O que representa estado, ação e recompensa.
8. Como o aprendizado é armazenado.
9. Como executar o sistema.
10. Como demonstrar cada agente.
11. Um exemplo de cenário para apresentação.

Inclua no README um cenário demonstrativo do agente cognitivo:

Temperatura = 29 °C
Temperatura desejada = 24 °C
Sem chuva
Janela fechada

O sistema compara, por exemplo:

Ar-condicionado:
boa redução de temperatura,
alto consumo de energia.

Janela + ventilador:
redução moderada,
baixo consumo.

E escolhe a opção com maior utilidade.

Também inclua um cenário demonstrativo do agente adaptativo:

Dia 1:
06:00 → agente abre janela → usuário rejeita → recompensa -1.

Dia 2:
06:00 → agente abre janela → usuário rejeita → recompensa -1.

Após algumas interações:
o valor da ação "abrir janela" naquele estado diminui.

Resultado:
o agente deixa de escolher essa ação naquele horário/contexto.

IMPORTANTE

Não faça uma reescrita desnecessária do projeto.

Trabalhe incrementalmente sobre os arquivos existentes.

Antes de implementar grandes mudanças, entenda as abstrações já existentes e mantenha compatibilidade com elas.

O resultado precisa ser simples o suficiente para eu conseguir explicar em uma apresentação de faculdade.

Evite abstrações excessivamente complexas.

Priorize código:
- organizado;
- legível;
- comentado;
- didático;
- fácil de demonstrar.

Ao terminar:

1. Liste todos os arquivos criados.
2. Liste todos os arquivos modificados.
3. Explique resumidamente a responsabilidade de cada arquivo.
4. Explique o fluxo do agente cognitivo.
5. Explique o fluxo do agente adaptativo.
6. Mostre como executar.
7. Mostre como testar manualmente os dois cenários principais.
8. Informe qualquer decisão técnica que tenha sido necessária por causa da estrutura original do projeto.