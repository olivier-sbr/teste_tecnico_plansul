# Respostas ao Questionário

## Parte 1 — Sobre o que você construiu

**1.1** Descreva em até 5 linhas o que o seu pipeline faz, como se estivesse explicando para alguém da equipe de faturamento que não é técnico.

O pipeline une o Excel da equipe com o arquivo do convênio, detecta divergências entre as duas fontes e consolida tudo em um dataset único. Com isso, renomeia os laudos PDF vinculando cada arquivo ao paciente e à cobrança correta. Por fim, gera um relatório Excel com resumo financeiro, alertas de inconsistência e lista de laudos não processados, e envia por e-mail automaticamente.

---

**1.2** Qual foi a etapa mais difícil de implementar? O que tornou ela difícil e como você resolveu?

O match de arquivos. Primeiro porque foi difícil achar bons parametros para os thresholds escrevi um script auxiliar para calibrar os valores com os dados reais. Segundo porque percebi que um laudo pode ter um nome de arquivo correto, mas estar errado internamente o arquivo passaria no critério de nome mas referenciaria um COB diferente do esperado. Resolvi deixando o match por nome bem estrito e adicionando uma validação que le o COB de dentro do PDF se for um cob em desacordo coma tabela, essa informação serve como um critério de desempate para não renomear o laudo, mas até chegar a essa ideia foram algums reruns onde eu tinha que manulmente abrir os pdfs e ver os laudos checando o novo nome com o cob escrito.

---

**1.3** A reconciliação entre o Excel e o CSV exigiu decisões sobre o que fazer quando os dados divergem. Descreva as principais decisões que você tomou:

- Quando o valor de uma cobrança difere entre as fontes, qual prevalece e por quê?

- O que você faz com uma cobrança que está só no CSV e não tem correspondente no Excel?
- Como você identificou que dois registros se referem ao mesmo paciente mesmo com grafias diferentes?

Quando há divergência de valor, o CSV prevalece por ser a fonte mais confiável, desconto a glosa do valor do excel antes de comparar e tolerei diferenças de até 0.25, por conta do contexto de arredondamentos do sistema legado.

Cobranças que aparecem só no CSV entram no dataset normalmente e são sinalizadas na aba de Alertas. Descartá-las seria jogar fora informações que poderiam ser importante para auditoria.

Para identificar o mesmo paciente com grafias diferentes, normalizei os nomes das duas fontes removendo acentos e convertendo para maiúsculas, sem sobrescrever os originais, o CSV armazena no formato "SOBRENOME, NOME", então inverti antes de comparar.

---

**1.4** Como você fez o vínculo entre os arquivos PDF e os registros de cobrança? Descreva a lógica de similaridade que usou, qual foi o maior risco dessa abordagem e como você o mitigou.

Normalizei o nome do arquivo e comparei contra os nomes dos pacientes usando rapidfuzz, que escolhi por a biblioteca que achei com mais documentação e facilidade para usar no desafio, pensei no jellyfish, mas descartei, porque vi que parecia ser melhor calibrado pro inglês e performaria mal em português. O score é composto de dois algoritmos combinados, passo o nome pelo ftfy para corrigir problemas de encoding — sem isso arquivos com acento pontuavam errado. Só aceito o match se o score passar do threshold e tiver gap suficiente pro segundo colocado. Depois ainda cruzo o dia e mês do arquivo com a data da cobrança no CSV. Por fim, leio o COB de dentro do PDF com pdfplumber e comparo com o esperado um arquivo pode ter nome com qualidade, mas ter sido gerado com cob incoerente no sistema legado.

---

**1.5** Houve algum dado nos arquivos que te surpreendeu ou que você não esperava encontrar? Como você tratou?

Quando fui fazer as checagens, comecei a encontrar laudos que possuiam COBS de outros pacientes, como a Carolina, o Carlos, eu sabia que os nomes poderiam ser ruíns por erro humano, mas quando iniciei o teste esqueci de considerar os laudos vindo com informações erradas, foi aqui que aplicei o filtro de cob.

Considerei pegar mais informações do laudo pra fazer quase todo o match de nomes com base nisso, mas achei que poderia estar indo contra as instruções do desafio, de dar o match com base no nome do arquivo.

---

## Parte 2 — Sobre as decisões técnicas

**2.1** Por que você escolheu a linguagem e as bibliotecas que usou? Quais alternativas considerou e por que descartou?

Usei Python costume e facilidade, visto que ja trabalhei em automações com python tanto profissionalmente quanto academicamente, e teria mais facilidade de aprender bibliotecas que não conheço. Pandas por ser a biblioteca mais consolidada, e por ja ter feito cursos relacionados e usado em ferramentas desenvolvidas no meu antigo trabalhom unidecode pelo mesmo motivo. Para o matching de nomes escolhi rapidfuzz pela documentação, parecia a alternativa com menor curva de aprendizado, considerei jellyfish mas vi que os algoritmos dele são mais voltados para o inglês e performariam pior com nomes brasileiros. Para gerar o Excel usei xlsxwriter em vez de openpyxl porque o pipeline só escreve, nunca lê o arquivo de volta, xlsxwriter parecia simples para esse caso e possuia algumas facilidades para aplicar autofilters no relatório, mesmo openpyxl sendo mais consolidado. Para o e-mail comecei com yagmail mas migrei para smtplib da stdlib porque o yagmail não dava controle suficiente sobre STARTTLS, o que causava falha de conexão com o Mailtrap na hora dos testes.

As outras bibliotecas como ftfy e pdfplumber eu conheci pesquisando soluções com auxilio de IA pros problemas que encontrei, não havia usado previamente.

---

**2.2** Como você organizou o código? Explique brevemente a estrutura que criou e por que ela faz sentido para este problema.

Separei o código em módulos por responsabilidade, reader só carrega os arquivos, preprocessing normaliza os dados, sourcemerger faz o merge e detecta divergências, pdfmapper cuida do vínculo e renomeação dos PDFs, reportwriter gera o excel e emailsender faz o envio. O main.py só orquestra a sequência, mas ao longo do teste ia desenvolvendo diretamente na main, apenas extraia quando percebia que fazia sentido e que a main estava acumulando responsabilidades desnecessárias.

Para o problema fazia sentido imaginar cada etapa como um processo fechado, cada um dos modulos pode ser imaginado como um bloco de processamento, e a main funciona como a linha que liga esses blocos.

---

**2.3** O pipeline lida com arquivos que podem chegar com problemas. Para cada cenário abaixo, descreva o que acontece no seu código:

- O Excel chega com uma coluna faltando
- Uma linha do CSV tem o campo `vl_liquido` vazio ou com texto no lugar do valor
- Dois PDFs na pasta `laudos/` têm nomes tão parecidos que o algoritmo de similaridade empata — ele não consegue decidir com certeza a qual cobrança cada um pertence
- O pipeline roda duas vezes seguidas sem que os arquivos de entrada tenham mudado

Não há validação no reader, o erro aparece mais pra frente sem contexto claro. O reportwriter valida antes de abrir o workspce, mas colunas usadas no merge quebrariam.

Falha na coluna inteira e o pipeline para. Valor genuinamente ausente sobreviveria como NaN e é ignorado nas somas.

Se o gap de score entre pacientes for menor que 10, nenhum é vinculado. Se os dois passam no critério de nome e data e resolvem para a mesma cobrança, o COB interno de cada PDF é lido como fator de desempate, se um bater, ele é renomeado e o outro descartado. Se o COB também não resolver, nenhum é renomeado e o conflito aparece nos alertas.

PDFs já copiados são pulados mas o mapeamento é registrado, então a coluna pdf_renomeado fica preenchida normalmente, o relatório é gerado de novo e o email é enviado novamente

---

**2.4** Se o pipeline fosse rodar em produção todo mês com arquivos reais, o que você mudaria ou reforçaria em relação ao que entregou?

Em produção o que mais geraria valor seria aumentar a cobertura de renomeação com um fallback por descrição de serviço para os laudos sem data no filename, hoje são a maior fatia dos não processados e ficam sem vinculo todo mês, mas não pensei exatamente como implementaria isso.

Separaria a falha de e-mail do exit 1, porque hoje uma falha SMTP derruba o pipeline mesmo com o relatório já gerado.

E ia adicionar uma validação das colunas na leitura dos arquivos para falhar cedo com mensagem clara, já que hoje um header diferente no CSV causa erro confuso no meio do processamento.

---

**2.5** Tem alguma parte do código que você sabe que não está boa, mas deixou assim por limitação de tempo? O que está errado e como você corrigiria?

O reportwriter foi o pior módulo na minha opinião, cresceu desordenado e ficou pouco reutilizável, com o mapeamento de colunas hardcodado, qualquer mudança de estrutura exige edição manual. No geral gostaria de ter adicionado mais tratamento de erro em vários pontos, mas priorizei o módulo de email por ser o mais crítico, uma falha de conexão sem tratamento derrubaria o pipeline no final.

---

## Parte 3 — Visão de evolução

**3.1** Hoje o pipeline é disparado manualmente via shell script. Se você fosse propor a próxima evolução de infraestrutura — considerando que a empresa usa servidores Linux (VPS) e não tem cloud — o que você sugeriria e por quê? Que problema concreto isso resolve que o cron não resolve?

Hoje uma forma mais moderna de rodar rotinas em Linux seria um service com systemd, utilizando timer. Teriamos melhoras logs, visto que com cron ficamos dependentes de um sistema de logs no software em si, ele reiniciaria sozinho em caso de falhas, garantindo que um gerente não ficasse sem relatórios por um erro de execução inesperado.

Não é a prova de falhas, mas o cronjob não é uma ferramenta desenvolvida pra automações robustas, é uma ferramenta de rotinas para scripts simples.

---

**3.2** Imagine que, além dos arquivos atuais, o departamento passasse a receber um XML de retorno do convênio com o resultado do processamento de cada cobrança — aprovada, glosada parcialmente ou negada, com o motivo. Como você integraria essa nova fonte ao pipeline existente? O que mudaria no relatório final?

Adicionaria um load_xml no reader e um normalize_xml no preprocessing seguindo o padrão já existente. O merge entraria depois do merge atual usando o mesmo id_cobranca como chave, com merge a esquerda para não perder cobranças sem retorno. As novas colunas resultado_convenio e motivo_glosa entrariam lista de headers, e o reportwriter ganharia condições para cobranças negadas. A mudança mais relevante no relatório seria separar alertas de inconsistência interna de cobranças efetivamente negadas pelo convênio.

---

**3.3** O relatório Excel hoje é enviado por e-mail para um gestor. Se a empresa quisesse evoluir para um painel web simples onde o gestor pudesse consultar o histórico de relatórios e filtrar por mês, convênio ou tipo de alerta — como você estruturaria isso? Não precisa implementar, só descrever a abordagem técnica.

O pipeline já roda no VPS via systemd, no final de cada execução salvaria os metadados e o caminho do relatório gerado em um banco local. Uma aplicação web no mesmo servidor leria esse banco e exibiria o histórico de execuções com filtros por mês, convênio e tipo de alerta, com download direto dos arquivos excel. Tudo no mesmo VPS, sem infraestrutura adicional, a pipeline processa e salva, a aplicação só consulta e retorna para o usuário.

---

**3.4** Quais métricas ou condições você monitoraria se esse pipeline estivesse em produção? Dê exemplos concretos do que deveria disparar uma notificação imediata para a equipe — e do que não deveria.

Alertaria para exit 1, dataset vazio após o merge, falha no envio do email e queda brusca no número de cobranças em relação ao mês anterior. Laudos não identificados, COB divergentes e ambíguos não alertariam, são casos esperados que já aparecem no relatório. A ideia é alertar só quando o resultado está comprometido, e não quando erro humano é monitorado e auditado pelas ferramentas da própria automação em si.

---

## Parte 4 — Uso de agentes de IA

**4.1** Você usou algum agente de IA para te ajudar a resolver o desafio? Se sim, para quais partes do processo você o utilizou e como?

Sim, usei o Claude Code como auxiliar durante o desenvolvimento.

Usava principalmente para acelerar implementação de partes que já tinha decidido como fazer, também em auxilio para debugar logs de erros, utilizar bibliotecas que não conhecia, como o rapidfuzz,conhecer novas bibliotecas. Também para acelerar o desenvolvimento do HTML do e-mail. As decisões de arquitetura e os critérios de negócio e requisitos do software foram meus, defini que zero renames errados era mais importante que cobertura, determinei o threshold e gap mínimo após rodar meu próprio script de calibração nos dados reais, e identifiquei o problema dos laudos com COB interno divergente rodando o pipeline e abrindo os arquivos manualmente. Quando o agente sugeriu abordagens que não funcionaram na prática, eu descartei e redirecionei.

Implementação do envio de email também foi, tarefas mais padrões e fáceis para o agente, mas decisões visão e idealização do projeto foram arquitetados por mim.

O claude também me ajudou criando um relatório para mim das decisões e resultados que eu possuia enquanto desenvolvia, para embasar e documentar pontos do desenvolvimento, visto que durou mais de um dia e eu eventualmente precisava consultar decisões anteriores.

---

## Parte 5 — Contexto pessoal

**5.1** Já trabalhou com automação de processos antes, mesmo que fora de um contexto profissional? Descreva brevemente o problema, o que você fez e qual foi o resultado.

Sim, no meu último estágio antes de formar como analista de suporte, eu oferecia ferramentas e automações para diversos times do P&D da empresa.

Desenvolvi um extrator de "coredumps", uma ferramenta que auxilíava os desenvolvedores a entenderem em que trecho do código fonte dos produtos da empresa havia ocorrido um "segfault", processo manual bem demorado que foi facilitado pela ferramenta, permitindo inclusive que membros do time de garantia de qualidade que não possuiam conhecimento de software pudessem extrair "coredumps" para investigação de bugs.

Também automatizei a geração de arquivoes de configuração de máquinas agricolas, soluções que eram conhecidas de problemas em campo não eram acessíveis pra técnicos de campo por envolverem conhecimento de software e linux, porém esses técnicos possuiam capacidade de diagnósticar os problemas sozinhos, mas havia um escalonamento de "issues" para que esse problema chegasse no time de suporte.

Desenvolvi uma plataforma para que o técnico apenas identificasse numa interface web o problema que ele possuia, passasse os parâmetros e baixasse um arquivo gerado automaticamente que ao ser instalado na máquina solucionava o problema dele.

---

**5.2** O que você faria diferente se tivesse o dobro do tempo para resolver este desafio?

## Mais logs de debugs, passaria todo projeto para uma arquitetura orientada a objetos, talvez exploraria os recursos de memória do pandas, mas principalmente, tentaria aumentar o coverage de laudos renomeados.

**5.3** Teve alguma parte do desafio que você achou mal especificada ou ambígua? O que estava faltando e como você lidou com a ambiguidade?

A parte mais ambígua foi o vínculo dos PDFs, o desafio diz que deve ser feito por similaridade do nome do arquivo, mas não especifica se informações extraídas do conteúdo interno poderiam complementar, decidi usar o COB lido do PDF apenas como critério de desempate depois que o vínculo por nome já estava estabelecido, não como método primário, porque interpretar o contrário parecia violar o requisito.

O desafio também não especifica onde salvar os PDFs renomeados, só o padrão do nome, criei uma pasta separada dos originais por segurança.

E não havia instrução sobre o que fazer com laudos sem correspondência, decidi criar uma aba dedicada no relatório com o motivo detalhado por arquivo, eu gostaria de, no output, ter uma pasta com PDFs não reprocessados, mas que possuiam nomes parecidos, ou então com os nomes identificados pelo pdfplumber. Mas achei que seria estranho o usuário copiar o PDF de um lugar e colar em outro, duplicando alguns arquivos, também não achei que seria responsável remover arquivos originais de /data.
