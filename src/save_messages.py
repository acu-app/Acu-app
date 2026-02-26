import os
import json
from src.narrative_v1 import build_client_messages


def save_messages_from_analysis_json(analysis_json_path: str) -> None:
    """
    Lee output/.../analysis.json y guarda:
    - whatsapp.txt
    - email.txt
    - simple.txt
    en la misma carpeta.
    """
    if not os.path.exists(analysis_json_path):
        raise FileNotFoundError(f"No existe: {analysis_json_path}")

    # carpeta del output (ej: output/2026-02-26)
    out_dir = os.path.dirname(analysis_json_path)

    with open(analysis_json_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    messages = build_client_messages(payload)

    # 1) WhatsApp
    whatsapp_path = os.path.join(out_dir, "whatsapp.txt")
    with open(whatsapp_path, "w", encoding="utf-8") as f:
        f.write(messages["whatsapp"])

    # 2) Email (subject + body)
    email_path = os.path.join(out_dir, "email.txt")
    with open(email_path, "w", encoding="utf-8") as f:
        f.write(f"Subject: {messages['email']['subject']}\n\n")
        f.write(messages["email"]["body"])

    # 3) Simple
    simple_path = os.path.join(out_dir, "simple.txt")
    with open(simple_path, "w", encoding="utf-8") as f:
        f.write(messages["simple"])

    print("✅ Mensajes guardados en:")
    print(" -", whatsapp_path)
    print(" -", email_path)
    print(" -", simple_path)
