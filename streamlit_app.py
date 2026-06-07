import streamlit as st
import random
import time

st.set_page_config(
    page_title="Exame de Código de Estrada - Portugal",
    page_icon="🚗",
    layout="centered",
)

BANCO_PERGUNTAS = [
    {
        "id": 1,
        "categoria": "Velocidades",
        "pergunta": "Qual é a velocidade máxima permitida numa autoestrada para veículos ligeiros?",
        "opcoes": ["100 km/h", "120 km/h", "130 km/h", "140 km/h"],
        "correta": 2,
        "explicacao": "Em autoestrada, a velocidade máxima para veículos ligeiros é 120 km/h.",
    },
    {
        "id": 2,
        "categoria": "Velocidades",
        "pergunta": "Qual é a velocidade máxima em localidade para veículos ligeiros?",
        "opcoes": ["30 km/h", "40 km/h", "50 km/h", "60 km/h"],
        "correta": 2,
        "explicacao": "Em localidade, a velocidade máxima para veículos ligeiros é 50 km/h, salvo sinalização em contrário.",
    },
    {
        "id": 3,
        "categoria": "Velocidades",
        "pergunta": "Qual é a velocidade máxima em estrada fora de localidade para veículos ligeiros?",
        "opcoes": ["80 km/h", "90 km/h", "100 km/h", "110 km/h"],
        "correta": 1,
        "explicacao": "Em estrada fora de localidade, a velocidade máxima para veículos ligeiros é 90 km/h.",
    },
    {
        "id": 4,
        "categoria": "Velocidades",
        "pergunta": "Nos primeiros 12 meses após a emissão da carta de condução, qual é a velocidade máxima numa autoestrada?",
        "opcoes": ["90 km/h", "100 km/h", "110 km/h", "120 km/h"],
        "correta": 1,
        "explicacao": "Os condutores novos (primeiros 12 meses) têm velocidade máxima de 100 km/h em autoestrada.",
    },
    {
        "id": 5,
        "categoria": "Álcool e Substâncias",
        "pergunta": "Qual é a taxa máxima de álcool no sangue (TAS) permitida para condutores em geral?",
        "opcoes": ["0,2 g/l", "0,5 g/l", "0,8 g/l", "1,0 g/l"],
        "correta": 1,
        "explicacao": "A TAS máxima permitida para condutores em geral é 0,5 g/l. Para condutores novos e profissionais é 0,2 g/l.",
    },
    {
        "id": 6,
        "categoria": "Álcool e Substâncias",
        "pergunta": "Qual é a taxa máxima de álcool no sangue (TAS) permitida para condutores novos (primeiros 3 anos) e profissionais?",
        "opcoes": ["0,0 g/l", "0,2 g/l", "0,3 g/l", "0,5 g/l"],
        "correta": 1,
        "explicacao": "Condutores novos (primeiros 3 anos) e profissionais têm TAS máxima de 0,2 g/l.",
    },
    {
        "id": 7,
        "categoria": "Prioridade",
        "pergunta": "Numa interseção sem sinalização, um veículo vindo da direita tem prioridade sobre:",
        "opcoes": [
            "Veículos da esquerda apenas",
            "Veículos da esquerda e em frente",
            "Todos os veículos",
            "Nenhum veículo",
        ],
        "correta": 0,
        "explicacao": "Numa interseção sem sinalização, tem prioridade o veículo que vem da direita relativamente ao veículo da esquerda.",
    },
    {
        "id": 8,
        "categoria": "Prioridade",
        "pergunta": "Qual dos seguintes veículos tem prioridade de passagem em qualquer situação?",
        "opcoes": [
            "Autocarros de linha",
            "Veículos pesados",
            "Veículos de socorro em missão de urgência",
            "Veículos com sinalização de prioridade",
        ],
        "correta": 2,
        "explicacao": "Os veículos de socorro (bombeiros, polícia, ambulância) em missão de urgência têm sempre prioridade de passagem.",
    },
    {
        "id": 9,
        "categoria": "Prioridade",
        "pergunta": "O sinal de STOP obriga o condutor a:",
        "opcoes": [
            "Abrandar e ceder passagem",
            "Parar completamente e ceder passagem",
            "Parar apenas se houver trânsito",
            "Abrandar para 10 km/h",
        ],
        "correta": 1,
        "explicacao": "O sinal de STOP (sinal B2) obriga à paragem completa antes da linha de paragem e a ceder passagem a todos os veículos.",
    },
    {
        "id": 10,
        "categoria": "Sinais",
        "pergunta": "O sinal de 'Cedência de passagem' (triângulo invertido) obriga o condutor a:",
        "opcoes": [
            "Parar completamente",
            "Ceder passagem sem necessidade de parar",
            "Diminuir a velocidade para 30 km/h",
            "Parar se houver trânsito em movimento",
        ],
        "correta": 1,
        "explicacao": "O sinal de cedência de passagem (B1) obriga a ceder passagem mas não exige paragem obrigatória, ao contrário do STOP.",
    },
    {
        "id": 11,
        "categoria": "Sinais",
        "pergunta": "Os sinais de proibição têm forma:",
        "opcoes": [
            "Triangular com vértice para cima",
            "Quadrada ou retangular",
            "Circular com fundo branco e orla vermelha",
            "Octogonal vermelha",
        ],
        "correta": 2,
        "explicacao": "Os sinais de proibição são circulares, com fundo branco e orla vermelha.",
    },
    {
        "id": 12,
        "categoria": "Sinais",
        "pergunta": "Os sinais de perigo têm forma:",
        "opcoes": [
            "Circular",
            "Triangular com vértice para cima e orla vermelha",
            "Quadrada azul",
            "Octogonal vermelha",
        ],
        "correta": 1,
        "explicacao": "Os sinais de perigo (avisos) são triangulares com vértice para cima e orla vermelha sobre fundo branco.",
    },
    {
        "id": 13,
        "categoria": "Sinais",
        "pergunta": "Os sinais de obrigação têm forma:",
        "opcoes": [
            "Triangular",
            "Circular com fundo azul",
            "Quadrada vermelha",
            "Retangular verde",
        ],
        "correta": 1,
        "explicacao": "Os sinais de obrigação são circulares com fundo azul (ex.: obrigatório seguir em frente).",
    },
    {
        "id": 14,
        "categoria": "Estacionamento e Paragem",
        "pergunta": "É proibido parar ou estacionar:",
        "opcoes": [
            "A mais de 5 metros de um cruzamento",
            "A menos de 5 metros de um cruzamento ou entroncamento",
            "A menos de 20 metros de um sinal de paragem obrigatória",
            "Em qualquer zona de localidade",
        ],
        "correta": 1,
        "explicacao": "É proibido parar ou estacionar a menos de 5 metros antes de um cruzamento ou entroncamento.",
    },
    {
        "id": 15,
        "categoria": "Estacionamento e Paragem",
        "pergunta": "Qual é a distância mínima a manter de uma paragem de autocarro ao estacionar?",
        "opcoes": ["5 metros", "10 metros", "15 metros", "20 metros"],
        "correta": 2,
        "explicacao": "É proibido estacionar a menos de 15 metros de uma paragem de autocarro.",
    },
    {
        "id": 16,
        "categoria": "Ultrapassagem",
        "pergunta": "Quando é proibido ultrapassar?",
        "opcoes": [
            "Em zonas de visibilidade reduzida marcadas com linha contínua",
            "Numa reta com boa visibilidade",
            "Fora de localidade em estrada de dois sentidos",
            "Quando o veículo da frente vai mais devagar",
        ],
        "correta": 0,
        "explicacao": "É proibido ultrapassar em zonas de visibilidade reduzida sinalizadas com linha longitudinal contínua ou dupla linha contínua.",
    },
    {
        "id": 17,
        "categoria": "Ultrapassagem",
        "pergunta": "Qual é o lado pelo qual se deve ultrapassar normalmente?",
        "opcoes": ["Pela direita", "Pela esquerda", "Pelo lado com mais espaço", "Qualquer lado"],
        "correta": 1,
        "explicacao": "A ultrapassagem deve ser feita pela esquerda, salvo exceções previstas no Código da Estrada.",
    },
    {
        "id": 18,
        "categoria": "Sinais Luminosos",
        "pergunta": "O que significa a luz amarela (âmbar) num semáforo?",
        "opcoes": [
            "Pode avançar com cautela",
            "Obriga a parar se puder fazê-lo em segurança",
            "Apenas avisa que o vermelho vai aparecer",
            "Tem o mesmo significado que o verde",
        ],
        "correta": 1,
        "explicacao": "A luz amarela num semáforo obriga a parar se o condutor o puder fazer em segurança antes da linha de paragem.",
    },
    {
        "id": 19,
        "categoria": "Sinais Luminosos",
        "pergunta": "O que significa a seta verde num semáforo com luz vermelha acesa?",
        "opcoes": [
            "Pode avançar em qualquer direção",
            "Pode avançar apenas na direção indicada pela seta, cedendo passagem",
            "Não pode avançar em nenhuma circunstância",
            "Pode avançar se não houver trânsito",
        ],
        "correta": 1,
        "explicacao": "A seta verde suplementar autoriza a circulação na direção indicada mesmo com vermelho, mas deve-se ceder passagem a peões e veículos com prioridade.",
    },
    {
        "id": 20,
        "categoria": "Segurança",
        "pergunta": "A utilização do cinto de segurança é obrigatória:",
        "opcoes": [
            "Apenas em autoestrada",
            "Fora de localidade",
            "Em todas as vias, em todos os lugares equipados com cinto",
            "Apenas para passageiros da frente",
        ],
        "correta": 2,
        "explicacao": "O uso do cinto de segurança é obrigatório em todos os lugares equipados com cinto, em qualquer tipo de via.",
    },
    {
        "id": 21,
        "categoria": "Segurança",
        "pergunta": "Até que idade as crianças devem usar sistema de retenção homologado (cadeirinha)?",
        "opcoes": [
            "Até aos 10 anos ou 1,35 m de altura",
            "Até aos 12 anos ou 1,35 m de altura",
            "Até aos 8 anos ou 1,20 m de altura",
            "Até aos 6 anos ou 1,20 m de altura",
        ],
        "correta": 1,
        "explicacao": "As crianças com menos de 135 cm de altura devem usar sistema de retenção adequado. Acima de 135 cm usam cinto de segurança normal.",
    },
    {
        "id": 22,
        "categoria": "Segurança",
        "pergunta": "O triângulo de pré-sinalização deve ser colocado a que distância mínima do obstáculo?",
        "opcoes": ["10 metros", "20 metros", "30 metros", "50 metros"],
        "correta": 2,
        "explicacao": "O triângulo de pré-sinalização deve ser colocado a pelo menos 30 metros do obstáculo em Portugal.",
    },
    {
        "id": 23,
        "categoria": "Documentos",
        "pergunta": "Quais são os documentos obrigatórios que o condutor deve transportar?",
        "opcoes": [
            "Carta de condução e bilhete de identidade",
            "Carta de condução, documento de identificação e documentos do veículo",
            "Apenas a carta de condução",
            "Carta de condução e seguro",
        ],
        "correta": 1,
        "explicacao": "O condutor deve transportar carta de condução, documento de identificação e documentos do veículo (livrete/DUA e seguro).",
    },
    {
        "id": 24,
        "categoria": "Iluminação",
        "pergunta": "Quando se devem usar as luzes de cruzamento (médios)?",
        "opcoes": [
            "Apenas à noite",
            "À noite em vias iluminadas e sempre que a visibilidade seja reduzida",
            "Apenas em vias não iluminadas",
            "Somente em autoestrada",
        ],
        "correta": 1,
        "explicacao": "As luzes de cruzamento (médios) devem ser usadas à noite em vias iluminadas, em condições de visibilidade reduzida e dentro das localidades.",
    },
    {
        "id": 25,
        "categoria": "Iluminação",
        "pergunta": "Quando devem ser usadas as luzes de máximos (estrada)?",
        "opcoes": [
            "Sempre à noite",
            "Apenas em autoestrada",
            "Fora de localidade à noite quando não haja veículos em sentido contrário nem à frente",
            "Em qualquer situação de visibilidade reduzida",
        ],
        "correta": 2,
        "explicacao": "As luzes de máximos (estrada) usam-se fora de localidade à noite, devendo ser substituídas pelas de cruzamento quando se aproxima trânsito no sentido contrário.",
    },
    {
        "id": 26,
        "categoria": "Circulação",
        "pergunta": "Em Portugal, a circulação faz-se:",
        "opcoes": [
            "Pelo lado direito da faixa de rodagem",
            "Pelo lado esquerdo da faixa de rodagem",
            "Pelo centro da faixa de rodagem",
            "Pelo lado mais conveniente",
        ],
        "correta": 0,
        "explicacao": "Em Portugal, a circulação faz-se pelo lado direito da faixa de rodagem, o mais próximo possível da berma ou passeio.",
    },
    {
        "id": 27,
        "categoria": "Rotundas",
        "pergunta": "Numa rotunda, quem tem prioridade?",
        "opcoes": [
            "Os veículos que entram na rotunda",
            "Os veículos que já circulam na rotunda",
            "O veículo mais à direita",
            "Os veículos pesados",
        ],
        "correta": 1,
        "explicacao": "Nas rotundas sinalizadas, têm prioridade os veículos que já circulam no interior da rotunda.",
    },
    {
        "id": 28,
        "categoria": "Rotundas",
        "pergunta": "Para sair de uma rotunda pela terceira saída, deve-se:",
        "opcoes": [
            "Circular sempre pela faixa da direita",
            "Circular pela faixa da esquerda e mudar para a direita antes de sair",
            "Circular pelo centro e sair diretamente",
            "Dar volta completa e sair pela direita",
        ],
        "correta": 1,
        "explicacao": "Para saídas mais à frente (esquerda), circula-se pela faixa esquerda e muda-se para a direita antes da saída pretendida, assinalando a mudança.",
    },
    {
        "id": 29,
        "categoria": "Pontos na Carta",
        "pergunta": "Com quantos pontos começa a carta de condução em Portugal?",
        "opcoes": ["6 pontos", "8 pontos", "12 pontos", "18 pontos"],
        "correta": 2,
        "explicacao": "A carta de condução em Portugal inicia-se com 12 pontos. A carta é cassada quando os pontos chegam a zero.",
    },
    {
        "id": 30,
        "categoria": "Pontos na Carta",
        "pergunta": "Durante o período probatório (primeiros 3 anos), com quantos pontos começa a carta?",
        "opcoes": ["6 pontos", "8 pontos", "12 pontos", "6 pontos com progressão"],
        "correta": 0,
        "explicacao": "No período probatório (3 anos), a carta começa com 6 pontos e pode atingir 12 após esse período sem infrações graves.",
    },
    {
        "id": 31,
        "categoria": "Distâncias de Segurança",
        "pergunta": "O que determina a distância de segurança a manter em relação ao veículo da frente?",
        "opcoes": [
            "Apenas a velocidade",
            "A velocidade, estado do pavimento e condições atmosféricas",
            "A distância mínima de 50 metros",
            "O tipo de veículo",
        ],
        "correta": 1,
        "explicacao": "A distância de segurança depende da velocidade, estado do pavimento, condições atmosféricas e estado do veículo.",
    },
    {
        "id": 32,
        "categoria": "Segurança",
        "pergunta": "É proibido conduzir enquanto se utiliza o telemóvel?",
        "opcoes": [
            "Sim, exceto com sistema mãos livres",
            "Não, é permitido sempre",
            "Apenas em autoestrada",
            "Apenas se for para receber chamadas",
        ],
        "correta": 0,
        "explicacao": "É proibido o uso do telemóvel enquanto conduz, exceto com sistema mãos livres. Esta infração desconta 2 pontos da carta.",
    },
    {
        "id": 33,
        "categoria": "Peões",
        "pergunta": "O condutor deve ceder passagem ao peão que:",
        "opcoes": [
            "Está na passadeira ou se prepara para a atravessar",
            "Está na berma da estrada",
            "Atravessa longe de passadeira",
            "Está parado no passeio",
        ],
        "correta": 0,
        "explicacao": "O condutor deve ceder passagem ao peão que esteja na passadeira ou que se prepare para a atravessar.",
    },
    {
        "id": 34,
        "categoria": "Peões",
        "pergunta": "Em vias sem passeio, os peões devem circular:",
        "opcoes": [
            "Pelo lado direito",
            "Pelo lado esquerdo, de frente para o trânsito",
            "Pelo centro",
            "Pelo lado que preferir",
        ],
        "correta": 1,
        "explicacao": "Em vias sem passeio, os peões devem circular pelo lado esquerdo da via, de frente para o trânsito que circula no mesmo sentido.",
    },
    {
        "id": 35,
        "categoria": "Ultrapassagem",
        "pergunta": "É obrigatório indicar a ultrapassagem com:",
        "opcoes": [
            "Buzina antes e luz de médios depois",
            "Pisca-pisca esquerdo antes, esquerdo durante e pisca-pisca direito ao reentrar",
            "Apenas pisca-pisca esquerdo",
            "Luzes de máximos intermitentes",
        ],
        "correta": 1,
        "explicacao": "Ao ultrapassar, deve-se indicar com pisca esquerdo antes de sair, manter durante a ultrapassagem e usar pisca direito ao reentrar na faixa.",
    },
    {
        "id": 36,
        "categoria": "Circulação",
        "pergunta": "Numa via com três faixas no mesmo sentido, a faixa do meio deve ser usada para:",
        "opcoes": [
            "Circular normalmente",
            "Ultrapassagem e circulação quando as outras estão congestionadas",
            "Apenas para veículos pesados",
            "Sempre que o condutor quiser",
        ],
        "correta": 1,
        "explicacao": "A faixa do meio (ou da esquerda) serve para ultrapassagem. A faixa da direita é para circulação normal.",
    },
    {
        "id": 37,
        "categoria": "Sinais",
        "pergunta": "O sinal de 'Fim de proibição' (círculo com linha diagonal) indica:",
        "opcoes": [
            "Início de proibição",
            "Que uma proibição anterior deixa de vigorar",
            "Zona de perigo",
            "Obrigação de parar",
        ],
        "correta": 1,
        "explicacao": "O sinal de fim de proibição (B34 e seguintes) indica que a proibição imposta anteriormente cessa a partir daquele ponto.",
    },
    {
        "id": 38,
        "categoria": "Iluminação",
        "pergunta": "As luzes de nevoeiro traseiras (stop de nevoeiro) só devem ser usadas:",
        "opcoes": [
            "Sempre que chover",
            "Apenas em autoestrada",
            "Quando a visibilidade é inferior a 50 metros",
            "Sempre à noite",
        ],
        "correta": 2,
        "explicacao": "As luzes de nevoeiro traseiras só devem ser usadas quando a visibilidade for inferior a 50 metros, pois encadeiam os condutores que vêm atrás.",
    },
    {
        "id": 39,
        "categoria": "Segurança",
        "pergunta": "O capacete é obrigatório para os utilizadores de:",
        "opcoes": [
            "Motociclos, ciclomotores e velocípedes a motor",
            "Apenas motociclos de grande cilindrada",
            "Motociclos e ciclomotores",
            "Qualquer veículo de duas rodas",
        ],
        "correta": 2,
        "explicacao": "O capacete é obrigatório para condutores e passageiros de motociclos e ciclomotores. Para bicicletas é obrigatório apenas em menores de 16 anos.",
    },
    {
        "id": 40,
        "categoria": "Avarias e Emergências",
        "pergunta": "Ao imobilizar o veículo por avaria numa via rápida ou autoestrada, o condutor deve:",
        "opcoes": [
            "Sair do veículo e tentar reparar na faixa de rodagem",
            "Ligar o pisca-pisca de emergência, colocar colete refletor, sair pelo lado direito e colocar triângulo",
            "Apenas acender as luzes de emergência",
            "Esperar dentro do veículo",
        ],
        "correta": 1,
        "explicacao": "Em caso de avaria: ligar luzes de emergência, calçar o colete refletor ANTES de sair, sair pelo lado da berma, colocar triângulo e se possível afastar-se da via.",
    },
    {
        "id": 41,
        "categoria": "Álcool e Substâncias",
        "pergunta": "A condução sob influência de substâncias psicotrópicas (droga) é:",
        "opcoes": [
            "Permitida em pequenas quantidades",
            "Proibida absolutamente e constitui crime",
            "Apenas uma contraordenação grave",
            "Permitida fora das localidades",
        ],
        "correta": 1,
        "explicacao": "A condução sob influência de estupefacientes ou substâncias psicotrópicas constitui crime, independentemente da quantidade.",
    },
    {
        "id": 42,
        "categoria": "Circulação",
        "pergunta": "Em caso de nevão ou gelo na estrada, o que deve fazer o condutor?",
        "opcoes": [
            "Aumentar a velocidade para evitar derrapagem",
            "Reduzir a velocidade, aumentar a distância de segurança e evitar travagens bruscas",
            "Ligar as luzes de máximos",
            "Seguir à mesma velocidade mas com mais atenção",
        ],
        "correta": 1,
        "explicacao": "Em pavimento com neve ou gelo, deve reduzir a velocidade, aumentar muito a distância de segurança e evitar acelerações e travagens bruscas.",
    },
    {
        "id": 43,
        "categoria": "Sinais",
        "pergunta": "O que significa um sinal de 'Zona de Estacionamento Condicionado' (disco azul)?",
        "opcoes": [
            "Proibição total de estacionar",
            "Estacionamento limitado no tempo definido no sinal",
            "Estacionamento grátis",
            "Estacionamento apenas para residentes",
        ],
        "correta": 1,
        "explicacao": "A zona de estacionamento condicionado (disco) impõe um tempo máximo de estacionamento indicado no sinal, normalmente marcado com disco.",
    },
    {
        "id": 44,
        "categoria": "Prioridade",
        "pergunta": "Os comboios/elétricos têm prioridade sobre:",
        "opcoes": [
            "Apenas peões",
            "Apenas veículos automóveis",
            "Todos os outros utilizadores da via, exceto veículos de socorro em missão",
            "Nenhum utilizador",
        ],
        "correta": 2,
        "explicacao": "Os comboios e elétricos têm prioridade sobre todos os utilizadores da via, exceto os veículos de emergência em missão.",
    },
    {
        "id": 45,
        "categoria": "Velocidades",
        "pergunta": "Qual a velocidade máxima para veículos pesados de mercadorias em autoestrada?",
        "opcoes": ["90 km/h", "100 km/h", "110 km/h", "120 km/h"],
        "correta": 0,
        "explicacao": "Os veículos pesados de mercadorias têm velocidade máxima de 90 km/h em autoestrada.",
    },
    {
        "id": 46,
        "categoria": "Circulação",
        "pergunta": "Numa via de sentido único, onde se deve circular?",
        "opcoes": [
            "Sempre pelo lado direito",
            "Pelo lado esquerdo quando possível",
            "De preferência pelo lado direito, mas pode usar qualquer faixa",
            "No centro da via",
        ],
        "correta": 2,
        "explicacao": "Numa via de sentido único, deve-se circular de preferência pela faixa da direita, mas pode usar outras faixas se necessário.",
    },
    {
        "id": 47,
        "categoria": "Segurança",
        "pergunta": "A fadiga ao volante:",
        "opcoes": [
            "Só afeta condutores após 10 horas de condução",
            "Aumenta o tempo de reação e pode causar acidentes",
            "Não é perigosa em autoestrada",
            "Pode ser combatida abrindo a janela",
        ],
        "correta": 1,
        "explicacao": "A fadiga aumenta significativamente o tempo de reação, pode causar adormecimento e é uma das principais causas de acidentes. Deve-se fazer pausas regulares.",
    },
    {
        "id": 48,
        "categoria": "Estacionamento e Paragem",
        "pergunta": "É proibido estacionar sobre:",
        "opcoes": [
            "Passeio alargado",
            "Passagem para peões",
            "Zona de estacionamento pago vazio",
            "Berma larga",
        ],
        "correta": 1,
        "explicacao": "É absolutamente proibido estacionar ou parar sobre passadeiras para peões.",
    },
    {
        "id": 49,
        "categoria": "Sinais",
        "pergunta": "O sinal 'Proibição de ultrapassar' proíbe a ultrapassagem de:",
        "opcoes": [
            "Todos os veículos",
            "Apenas veículos pesados",
            "Veículos a motor, exceto motociclos de duas rodas sem carro lateral",
            "Apenas veículos lentos",
        ],
        "correta": 2,
        "explicacao": "O sinal de proibição de ultrapassar (C13a) proíbe a ultrapassagem de veículos a motor, exceto motociclos de duas rodas sem carro lateral.",
    },
    {
        "id": 50,
        "categoria": "Circulação",
        "pergunta": "O que é a 'corredor de emergência' na autoestrada?",
        "opcoes": [
            "Uma faixa exclusiva para veículos de emergência sempre presente",
            "Um espaço criado pelos condutores ao aproximar-se dos bordos para deixar passagem aos veículos de emergência",
            "A berma de emergência",
            "Uma faixa de circulação lenta",
        ],
        "correta": 1,
        "explicacao": "O corredor de emergência é criado pelos condutores em trânsito parado: os da esquerda aproximam-se da esquerda e os das restantes faixas da direita.",
    },
]


def init_state():
    if "fase" not in st.session_state:
        st.session_state.fase = "inicio"
    if "perguntas" not in st.session_state:
        st.session_state.perguntas = []
    if "idx" not in st.session_state:
        st.session_state.idx = 0
    if "respostas" not in st.session_state:
        st.session_state.respostas = {}
    if "inicio_ts" not in st.session_state:
        st.session_state.inicio_ts = None
    if "respondida" not in st.session_state:
        st.session_state.respondida = False
    if "opcao_selecionada" not in st.session_state:
        st.session_state.opcao_selecionada = None


def iniciar_exame():
    selecionadas = random.sample(BANCO_PERGUNTAS, min(30, len(BANCO_PERGUNTAS)))
    st.session_state.perguntas = selecionadas
    st.session_state.idx = 0
    st.session_state.respostas = {}
    st.session_state.inicio_ts = time.time()
    st.session_state.fase = "exame"
    st.session_state.respondida = False
    st.session_state.opcao_selecionada = None


def calcular_resultado():
    certas = 0
    for i, p in enumerate(st.session_state.perguntas):
        if st.session_state.respostas.get(i) == p["correta"]:
            certas += 1
    return certas


init_state()

st.markdown(
    """
    <style>
    .titulo-exame { font-size: 2rem; font-weight: bold; color: #1a3a6b; text-align: center; }
    .subtitulo { font-size: 1rem; color: #555; text-align: center; margin-bottom: 1rem; }
    .pergunta-box { background: #f0f4ff; border-left: 5px solid #1a3a6b; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; }
    .progresso { font-size: 0.9rem; color: #888; }
    .correto { color: #28a745; font-weight: bold; }
    .errado { color: #dc3545; font-weight: bold; }
    .explicacao { background: #fff8e1; border-left: 4px solid #ffc107; padding: 0.8rem; border-radius: 6px; margin-top: 0.5rem; }
    .resultado-aprovado { background: #d4edda; border: 2px solid #28a745; padding: 1.5rem; border-radius: 10px; text-align: center; }
    .resultado-reprovado { background: #f8d7da; border: 2px solid #dc3545; padding: 1.5rem; border-radius: 10px; text-align: center; }
    </style>
""",
    unsafe_allow_html=True,
)

# ─── FASE: INÍCIO ─────────────────────────────────────────────────────────────
if st.session_state.fase == "inicio":
    st.markdown('<div class="titulo-exame">🚗 Exame de Código de Estrada</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitulo">Simulação oficial — Portugal</div>', unsafe_allow_html=True)
    st.divider()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Perguntas", "30")
    with col2:
        st.metric("Tempo", "30 min")
    with col3:
        st.metric("Mínimo para aprovação", "25/30")

    st.divider()
    st.markdown("""
    **Regras do exame:**
    - 30 perguntas de escolha múltipla
    - Tempo limite: 30 minutos
    - Aprovação: mínimo 25 respostas certas (≥ 83%)
    - Cada pergunta tem apenas uma resposta correta
    - Não é possível voltar atrás após confirmar a resposta
    """)

    st.divider()
    if st.button("▶️  Iniciar Exame", type="primary", use_container_width=True):
        iniciar_exame()
        st.rerun()

# ─── FASE: EXAME ──────────────────────────────────────────────────────────────
elif st.session_state.fase == "exame":
    total = len(st.session_state.perguntas)
    idx = st.session_state.idx

    # Cronómetro
    elapsed = time.time() - st.session_state.inicio_ts
    remaining = max(0, 30 * 60 - elapsed)
    minutos = int(remaining // 60)
    segundos = int(remaining % 60)

    if remaining == 0:
        st.session_state.fase = "resultado"
        st.rerun()

    # Header
    col_prog, col_timer = st.columns([3, 1])
    with col_prog:
        st.markdown(f'<div class="progresso">Pergunta {idx + 1} de {total}</div>', unsafe_allow_html=True)
        st.progress((idx) / total)
    with col_timer:
        cor_timer = "#dc3545" if minutos < 5 else "#1a3a6b"
        st.markdown(
            f'<div style="text-align:right; font-size:1.3rem; font-weight:bold; color:{cor_timer};">⏱️ {minutos:02d}:{segundos:02d}</div>',
            unsafe_allow_html=True,
        )

    pergunta = st.session_state.perguntas[idx]
    st.markdown(
        f'<div class="pergunta-box"><b>Categoria: {pergunta["categoria"]}</b><br><br>{pergunta["pergunta"]}</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.respondida:
        opcao = st.radio(
            "Selecione a sua resposta:",
            options=range(len(pergunta["opcoes"])),
            format_func=lambda i: pergunta["opcoes"][i],
            key=f"radio_{idx}",
            index=None,
        )

        if st.button("✅ Confirmar Resposta", type="primary", disabled=(opcao is None)):
            st.session_state.respostas[idx] = opcao
            st.session_state.respondida = True
            st.session_state.opcao_selecionada = opcao
            st.rerun()
    else:
        opcao_dada = st.session_state.opcao_selecionada
        correta = pergunta["correta"]

        for i, opt in enumerate(pergunta["opcoes"]):
            if i == correta and i == opcao_dada:
                st.success(f"✅ {opt}")
            elif i == correta:
                st.success(f"✅ {opt}  ← Resposta correta")
            elif i == opcao_dada:
                st.error(f"❌ {opt}  ← A sua resposta")
            else:
                st.write(f"   {opt}")

        st.markdown(
            f'<div class="explicacao">💡 <b>Explicação:</b> {pergunta["explicacao"]}</div>',
            unsafe_allow_html=True,
        )

        col_a, col_b = st.columns(2)
        with col_a:
            if idx < total - 1:
                if st.button("➡️  Próxima Pergunta", type="primary", use_container_width=True):
                    st.session_state.idx += 1
                    st.session_state.respondida = False
                    st.session_state.opcao_selecionada = None
                    st.rerun()
            else:
                if st.button("🏁  Ver Resultado Final", type="primary", use_container_width=True):
                    st.session_state.fase = "resultado"
                    st.rerun()
        with col_b:
            if st.button("⏹️  Terminar Exame", use_container_width=True):
                # Marca perguntas não respondidas como erradas
                for i in range(total):
                    if i not in st.session_state.respostas:
                        st.session_state.respostas[i] = -1
                st.session_state.fase = "resultado"
                st.rerun()

    # Auto-refresh para o timer
    time.sleep(0.5)
    st.rerun()

# ─── FASE: RESULTADO ──────────────────────────────────────────────────────────
elif st.session_state.fase == "resultado":
    certas = calcular_resultado()
    total = len(st.session_state.perguntas)
    erradas = total - certas
    percentagem = (certas / total) * 100
    aprovado = certas >= 25

    st.markdown('<div class="titulo-exame">📋 Resultado do Exame</div>', unsafe_allow_html=True)
    st.divider()

    if aprovado:
        st.markdown(
            f"""
            <div class="resultado-aprovado">
                <h2>✅ APROVADO</h2>
                <h3>{certas}/{total} respostas certas ({percentagem:.1f}%)</h3>
                <p>Parabéns! Passou no exame de código de estrada.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="resultado-reprovado">
                <h2>❌ REPROVADO</h2>
                <h3>{certas}/{total} respostas certas ({percentagem:.1f}%)</h3>
                <p>São necessárias pelo menos 25 respostas certas. Tente novamente!</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Certas", certas, delta=None)
    with col2:
        st.metric("Erradas", erradas, delta=None)
    with col3:
        st.metric("Percentagem", f"{percentagem:.1f}%")

    # Estatísticas por categoria
    st.subheader("Desempenho por Categoria")
    categorias = {}
    for i, p in enumerate(st.session_state.perguntas):
        cat = p["categoria"]
        if cat not in categorias:
            categorias[cat] = {"certas": 0, "total": 0}
        categorias[cat]["total"] += 1
        if st.session_state.respostas.get(i) == p["correta"]:
            categorias[cat]["certas"] += 1

    for cat, dados in sorted(categorias.items()):
        pct = (dados["certas"] / dados["total"]) * 100
        icon = "✅" if pct >= 70 else "⚠️" if pct >= 50 else "❌"
        st.write(f"{icon} **{cat}**: {dados['certas']}/{dados['total']} ({pct:.0f}%)")

    # Revisão das respostas erradas
    erradas_lista = [
        (i, p) for i, p in enumerate(st.session_state.perguntas) if st.session_state.respostas.get(i) != p["correta"]
    ]
    if erradas_lista:
        st.divider()
        st.subheader(f"📚 Revisão das {len(erradas_lista)} respostas erradas")
        for i, p in erradas_lista:
            with st.expander(f"❌ P{i+1}: {p['pergunta'][:70]}..."):
                resp_dada = st.session_state.respostas.get(i, -1)
                if resp_dada >= 0:
                    st.error(f"A sua resposta: **{p['opcoes'][resp_dada]}**")
                else:
                    st.error("Não respondida")
                st.success(f"Resposta correta: **{p['opcoes'][p['correta']]}**")
                st.info(f"💡 {p['explicacao']}")

    st.divider()
    if st.button("🔄  Fazer Novo Exame", type="primary", use_container_width=True):
        for key in ["fase", "perguntas", "idx", "respostas", "inicio_ts", "respondida", "opcao_selecionada"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
