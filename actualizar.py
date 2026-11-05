"""Lo ejecuta GitHub cada 20 minutos: actualiza seguidores.json con TikTok y YouTube.

Instagram sale de manual.json, que se cambia desde el PC (actualizar_seguidores.py --instagram N).
seguidores.json solo lo escribe GitHub y manual.json solo el PC: así nunca chocan.
No usa nada de fuera de esta carpeta ni ningún secreto.
"""
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ARCHIVO = Path(__file__).resolve().parent / "seguidores.json"
MANUAL = ARCHIVO.with_name("manual.json")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"


def pagina(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def tiktok(usuario):
    m = re.search(r'"followerCount":(\d+)', pagina(f"https://www.tiktok.com/@{usuario}"))
    return int(m.group(1)) if m else None


def youtube(usuario):
    m = re.search(r'"([\d.]+)([KM]?) subscribers"', pagina(f"https://www.youtube.com/@{usuario}"))
    return round(float(m.group(1)) * {"": 1, "K": 1_000, "M": 1_000_000}[m.group(2)]) if m else None


LECTORES = {"tiktok": tiktok, "youtube": youtube}


def main():
    datos = json.loads(ARCHIVO.read_text(encoding="utf-8-sig"))
    manual = json.loads(MANUAL.read_text(encoding="utf-8-sig")) if MANUAL.exists() else {}
    cambios = False
    for red in datos["redes"]:
        lector = LECTORES.get(red["red"])
        if not lector:
            if manual.get(red["red"]) and manual[red["red"]] != red["seguidores"]:
                red["seguidores"] = manual[red["red"]]
                cambios = True
            continue
        try:
            n = lector(red["usuario"])
        except Exception as e:
            print(f"{red['red']}: no se pudo leer ({e})")
            continue
        print(f"{red['red']}: {n}")
        # Un 0 o nada suele ser un bloqueo puntual, no que hayas perdido a todos: se ignora.
        if n and n != red["seguidores"]:
            red["seguidores"] = n
            cambios = True
    if cambios:
        datos["actualizado"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        ARCHIVO.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
