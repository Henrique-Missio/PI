"""Envio de email — recuperacao de senha. Config via env vars.
Sem SMTP_HOST configurado, cai em modo dev (so loga no console)."""
import os
import smtplib
import logging
from email.mime.text import MIMEText

logger = logging.getLogger("pidstech.email")

SMTP_HOST = os.environ.get("SMTP_HOST")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")
SMTP_REMETENTE = os.environ.get("SMTP_REMETENTE", SMTP_USER or "no-reply@pidstech.local")


def enviar_email(destinatario: str, assunto: str, corpo: str) -> bool:
    """True se enviado (ou impresso em modo dev). False se erro real de envio."""
    if not SMTP_HOST:
        print(f"\n[EMAIL DEV] Para: {destinatario} | Assunto: {assunto}\n{corpo}\n", flush=True)
        return True

    msg = MIMEText(corpo)
    msg["Subject"] = assunto
    msg["From"] = SMTP_REMETENTE
    msg["To"] = destinatario

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as servidor:
            servidor.starttls()
            if SMTP_USER and SMTP_PASS:
                servidor.login(SMTP_USER, SMTP_PASS)
            servidor.sendmail(SMTP_REMETENTE, [destinatario], msg.as_string())
        return True
    except Exception:
        logger.exception("Falha ao enviar email para %s", destinatario)
        return False


def enviar_codigo_recuperacao(destinatario: str, codigo: str) -> bool:
    assunto = "Pids Tech — Código de recuperação de senha"
    corpo = (
        f"Seu código de recuperação de senha é: {codigo}\n\n"
        f"Esse código expira em 15 minutos. Se você não solicitou, ignore este email."
    )
    return enviar_email(destinatario, assunto, corpo)
