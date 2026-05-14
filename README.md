# Pipeline de Faturamento — Plansul

Lê dois arquivos de cobrança (Excel + CSV), detecta divergências, renomeia os laudos PDF e gera um relatório Excel. No final envia o relatório por e-mail.

---

## Requisitos

- Python 3.12+

---

## Instalação

```bash
git clone https://github.com/olivier-sbr/teste_tecnico_plansul.git
cd teste_tecnico_plansul

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

---

## Configuração

Copie o arquivo de exemplo e preencha com suas credenciais:

```bash
cp .env.example .env
```

### Gmail (recomendado)

O Gmail não aceita a senha normal via SMTP — é necessário gerar uma **App Password**:

1. Acesse [myaccount.google.com](https://myaccount.google.com)
2. Segurança → Verificação em duas etapas (precisa estar ativa)
3. Segurança → Senhas de app → selecione "Outro" → gere
4. Copie a senha de 16 caracteres gerada (formato `xxxx xxxx xxxx xxxx`)

```
EMAIL_USER=seu@gmail.com
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx
EMAIL_TO=destinatario@exemplo.com
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
```

### Mailtrap (sandbox — recebe sem enviar de verdade)

Útil para testar sem risco de enviar e-mail real. Crie uma conta gratuita em [mailtrap.io](https://mailtrap.io):

1. Acesse **Email Testing → Inboxes**
2. Clique no inbox padrão → aba **SMTP Settings**
3. Copie usuário, senha, host e porta

```
EMAIL_USER=usuario_mailtrap
EMAIL_PASSWORD=senha_mailtrap
EMAIL_TO=qualquer@email.com
EMAIL_HOST=sandbox.smtp.mailtrap.io
EMAIL_PORT=2525
```

Os e-mails enviados aparecem no inbox do Mailtrap — nenhum destinatário real é atingido.

---

## Execução

```bash
chmod +x run.sh
bash run.sh
```

O log fica em `output/logs/pipeline_YYYYMMDD_HHMMSS.log`.  
O relatório gerado fica em `output/relatorio_faturamento_YYYYMM.xlsx`.
