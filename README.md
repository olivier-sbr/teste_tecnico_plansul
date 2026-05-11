# Teste Técnico — Desenvolvedor de Automação Júnior

Pipeline de automação do processo de faturamento hospitalar: consolida cobranças de duas fontes, renomeia laudos PDF, gera relatório Excel e envia por e-mail.

---

## Requisitos

- Python 3.12+

---

## Instalação

**1. Clone o repositório**

```bash
git clone https://github.com/olivier-sbr/teste_tecnico_plansul.git
cd teste_tecnico_plansul
```

**2. Crie e ative o virtual environment**

```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
```

**3. Instale as dependências**

```bash
pip install -r requirements.txt
```

**4. Configure as variáveis de ambiente**

```bash
cp .env.example .env
```

---

## Execução

```bash
bash run.sh
```

O script ativa o virtual environment, executa o pipeline e salva o log em `output/logs/` com timestamp.
