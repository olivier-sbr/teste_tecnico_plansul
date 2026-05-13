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

### Gmail

Use uma **App Password** — a senha normal não funciona com SMTP.  
Para gerar: conta Google → Segurança → Verificação em duas etapas → Senhas de app.

```
EMAIL_USER=seu@gmail.com
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx
EMAIL_TO=destinatario@exemplo.com
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
```

### Mailtrap (sandbox, sem envio real)

Crie uma conta em [mailtrap.io](https://mailtrap.io), abra o inbox de sandbox e copie as credenciais SMTP da aba **SMTP Settings**.

```
EMAIL_USER=usuario_mailtrap
EMAIL_PASSWORD=senha_mailtrap
EMAIL_TO=qualquer@email.com
EMAIL_HOST=sandbox.smtp.mailtrap.io
EMAIL_PORT=2525
```

---

## Execução

```bash
bash run.sh
```

O log fica em `output/logs/pipeline_YYYYMMDD_HHMMSS.log`.  
O relatório gerado fica em `output/relatorio_faturamento_YYYYMM.xlsx`.
