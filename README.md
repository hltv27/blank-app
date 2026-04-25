# blank-app

Uma aplicação Python com interface web construída com [Streamlit](https://streamlit.io/).

## Descrição

Este projecto serve de ponto de partida para aplicações Python interactivas. Utiliza o Streamlit para criar interfaces web de forma simples, sem necessidade de HTML ou JavaScript.

## Estrutura do Projecto

```
blank-app/
├── main.py              # Ponto de entrada da aplicação
├── streamlit_app.py     # Interface web Streamlit
├── requirements.txt     # Dependências Python
└── README.md            # Este ficheiro
```

## Requisitos

- Python 3.8+
- pip

## Instalação

```bash
# Clonar o repositório
git clone https://github.com/hltv27/blank-app.git
cd blank-app

# Criar e activar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Instalar dependências
pip install -r requirements.txt
```

## Como Executar

**Aplicação principal (linha de comandos):**

```bash
python main.py
```

**Interface web Streamlit:**

```bash
streamlit run streamlit_app.py
```

## Desenvolvimento

Para adicionar dependências:

```bash
pip install <pacote>
pip freeze > requirements.txt
```

## Licença

Consulte o ficheiro [LICENSE](LICENSE) para detalhes.
