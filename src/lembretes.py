import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

FUSO = ZoneInfo("America/Sao_Paulo")
ARQUIVO = Path(__file__).resolve().parent.parent / "dados" / "lembretes.json"


def agora():
    return datetime.now(FUSO)


def carregar():
    if not ARQUIVO.exists():
        return []
    try:
        return json.loads(ARQUIVO.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def salvar(lista):
    ARQUIVO.parent.mkdir(exist_ok=True)
    texto = json.dumps(lista, ensure_ascii=False, indent=2)
    ARQUIVO.write_text(texto, encoding="utf-8")


def interpretar(args):
    """Entende: [DD/MM[/AAAA]] HH:MM texto. Devolve (datetime, texto)."""
    args = list(args)
    data = None
    if args and re.fullmatch(r"\d{1,2}/\d{1,2}(/\d{4})?", args[0]):
        data = args.pop(0)
    if not args or not re.fullmatch(r"\d{1,2}:\d{2}", args[0]):
        raise ValueError("hora")
    hora, minuto = map(int, args.pop(0).split(":"))
    texto = " ".join(args).strip()
    if not texto:
        raise ValueError("texto")

    hoje = agora()
    if data:
        partes = data.split("/")
        dia, mes = int(partes[0]), int(partes[1])
        ano = int(partes[2]) if len(partes) == 3 else hoje.year
        quando = datetime(ano, mes, dia, hora, minuto, tzinfo=FUSO)
        if len(partes) < 3 and quando <= hoje:
            quando = quando.replace(year=ano + 1)
    else:
        quando = hoje.replace(hour=hora, minute=minuto, second=0, microsecond=0)
        if quando <= hoje:
            quando += timedelta(days=1)
    return quando, texto