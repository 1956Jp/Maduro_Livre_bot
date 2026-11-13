#!/usr/bin/env python3
"""Descarga imagenes libres (Wikimedia Commons) para el bot Maduro_Livre.

Uso:
    .venv/bin/python descargar_imagenes.py

Crea / actualiza:
    imagenes/<tema>/<archivo>.jpg
    imagenes/<tema>/creditos.txt
    imagenes/indice.json

Solo descarga imagenes con licencias libres (dominio publico / CC0 / CC BY /
CC BY-SA). Las imagenes que coloques manualmente en imagenes/<tema>/ tambien
son utilizadas por el bot; este script nunca borra nada.
"""
import html
import json
import os
import re
import unicodedata
import urllib.parse

import httpx

BASE = os.path.dirname(os.path.abspath(__file__))
DESTINO = os.path.join(BASE, "imagenes")
API = "https://commons.wikimedia.org/w/api.php"
UA = "MaduroLivreBot/1.0 (https://t.me/jose129_bot)"
EXTENSIONES = (".jpg", ".jpeg", ".png", ".webp")
EXT_POR_MIME = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
PALABRAS_IGNORADAS = {
    "file", "jpg", "jpeg", "png", "webp", "the", "and", "for", "with", "from",
    "del", "los", "las", "una", "uno", "por", "con", "que", "jpg",
}

# Terminos de busqueda por tema (se combinan).
TEMAS = {
    "maduro": [
        "Nicolás Maduro",
        "Nicolas Maduro Moros",
        "Nicolás Maduro 2023",
    ],
    "cilia_flores": [
        "Cilia Flores",
    ],
    "comunas": [
        "consejo comunal",
        "Misión Vivienda",
        "comuna Venezuela",
        "poder popular Venezuela",
    ],
}

RESULTADOS_POR_TERMINO = 6
MAX_POR_TEMA = 8
LICENCIAS_OK = ("public domain", "cc0", "cc by", "cc-by", "cc by-sa", "cc-by-sa")
LICENCIAS_NO = ("fair use", "non-free", "nonfree", "copyright")


def normalizar(texto: str) -> str:
    """Minusculas sin acentos, para comparar palabras clave."""
    texto = unicodedata.normalize("NFKD", texto or "")
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto.lower()


def sin_html(texto: str) -> str:
    texto = re.sub(r"<[^>]+>", " ", texto or "")
    return re.sub(r"\s+", " ", html.unescape(texto)).strip()


def slug(texto: str) -> str:
    texto = normalizar(texto).replace("file:", "")
    texto = re.sub(r"\.(jpe?g|png|webp)$", "", texto)
    texto = re.sub(r"[^a-z0-9]+", "_", texto).strip("_")
    return texto[:60].strip("_") or "imagen"


def palabras_de(*textos: str):
    palabras = set()
    for t in textos:
        for p in re.findall(r"[a-z0-9áéíóúñ]{3,}", normalizar(t)):
            if p not in PALABRAS_IGNORADAS and not p.isdigit():
                palabras.add(p)
    return sorted(palabras)


def buscar(client: httpx.Client, termino: str):
    """Devuelve titulos de archivo (namespace 6) para un termino."""
    params = {
        "action": "query",
        "list": "search",
        "srsearch": f"filetype:bitmap {termino}",
        "srnamespace": "6",
        "srlimit": str(RESULTADOS_POR_TERMINO),
        "format": "json",
    }
    r = client.get(API, params=params)
    r.raise_for_status()
    return [m["title"] for m in r.json().get("query", {}).get("search", [])]


def informacion(client: httpx.Client, titulos):
    """Devuelve metadatos (url, mime, licencia, autor, descripcion) por titulo."""
    if not titulos:
        return []
    params = {
        "action": "query",
        "titles": "|".join(titulos),
        "prop": "imageinfo",
        "iiprop": "url|mime|extmetadata",
        "iiurlwidth": "800",
        "format": "json",
    }
    r = client.get(API, params=params)
    r.raise_for_status()
    salida = []
    for pagina in r.json().get("query", {}).get("pages", {}).values():
        info = (pagina.get("imageinfo") or [{}])[0]
        if not info:
            continue
        em = info.get("extmetadata", {})
        licencia = sin_html(em.get("LicenseShortName", {}).get("value", ""))
        autor = sin_html(em.get("Artist", {}).get("value", ""))
        descripcion = sin_html(em.get("ImageDescription", {}).get("value", ""))
        salida.append(
            {
                "titulo": pagina["title"],
                "url": info.get("thumburl") or info.get("url"),
                "mime": info.get("mime", ""),
                "licencia": licencia,
                "autor": autor,
                "descripcion": descripcion,
                "pagina": info.get("descriptionurl", ""),
            }
        )
    return salida


def licencia_valida(licencia: str) -> bool:
    texto = normalizar(licencia)
    if not texto:
        return False
    if any(mal in texto for mal in LICENCIAS_NO):
        return False
    return any(ok in texto for ok in LICENCIAS_OK)


def descargar(client: httpx.Client, url: str, destino: str) -> bool:
    try:
        r = client.get(url)
        r.raise_for_status()
        if b"<html" in r.content[:200].lower():
            return False
        with open(destino, "wb") as fh:
            fh.write(r.content)
        return os.path.getsize(destino) > 5000
    except Exception as e:  # noqa: BLE001
        print(f"    ! error descargando {url}: {e}")
        return False


def main():
    indice = {}
    with httpx.Client(headers={"User-Agent": UA}, timeout=30, follow_redirects=True) as client:
        for tema, terminos in TEMAS.items():
            carpeta = os.path.join(DESTINO, tema)
            os.makedirs(carpeta, exist_ok=True)
            print(f"\n== {tema} ==")
            vistos = set()
            archivos = []
            for termino in terminos:
                if len(archivos) >= MAX_POR_TEMA:
                    break
                print(f"  buscando: {termino}")
                try:
                    titulos = buscar(client, termino)
                except Exception as e:  # noqa: BLE001
                    print(f"    ! error de busqueda: {e}")
                    continue
                for meta in informacion(client, titulos):
                    if len(archivos) >= MAX_POR_TEMA:
                        break
                    if meta["titulo"] in vistos:
                        continue
                    vistos.add(meta["titulo"])
                    if meta["mime"] not in ("image/jpeg", "image/png", "image/webp"):
                        continue
                    if not licencia_valida(meta["licencia"]):
                        print(f"    - omitido (licencia {meta['licencia'] or '?'}): {meta['titulo']}")
                        continue
                    nombre = slug(meta["titulo"]) + EXT_POR_MIME[meta["mime"]]
                    if nombre in vistos:
                        continue
                    vistos.add(nombre)
                    destino = os.path.join(carpeta, nombre)
                    if os.path.isfile(destino):
                        archivos.append((nombre, meta))
                        continue
                    if not meta["url"]:
                        continue
                    if descargar(client, meta["url"], destino):
                        print(f"    + {nombre}")
                        archivos.append((nombre, meta))
                    else:
                        print(f"    - fallo al descargar: {meta['titulo']}")
            # creditos legibles
            with open(os.path.join(carpeta, "creditos.txt"), "w", encoding="utf-8") as fh:
                for nombre, meta in archivos:
                    fh.write(
                        f"{nombre} | {sin_html(meta['titulo'])} | "
                        f"{meta['autor'] or 'desconocido'} | {meta['licencia']} | {meta['pagina']}\n"
                    )
            indice[tema] = [
                {
                    "archivo": nombre,
                    "titulo": sin_html(meta["titulo"]),
                    "autor": meta["autor"],
                    "licencia": meta["licencia"],
                    "pagina": meta["pagina"],
                    "palabras": palabras_de(meta["titulo"], meta["descripcion"], meta["autor"]),
                }
                for nombre, meta in archivos
            ]

    # incorpora imagenes colocadas manualmente y no listadas en el indice
    for tema in TEMAS:
        carpeta = os.path.join(DESTINO, tema)
        if not os.path.isdir(carpeta):
            continue
        conocidos = {item["archivo"] for item in indice.get(tema, [])}
        for nombre in sorted(os.listdir(carpeta)):
            if nombre.lower().endswith(EXTENSIONES) and nombre not in conocidos:
                indice.setdefault(tema, []).append(
                    {"archivo": nombre, "titulo": nombre, "autor": "", "licencia": "", "pagina": "", "palabras": palabras_de(nombre)}
                )

    with open(os.path.join(DESTINO, "indice.json"), "w", encoding="utf-8") as fh:
        json.dump(indice, fh, ensure_ascii=False, indent=2)
    print("\nIndice escrito en imagenes/indice.json")
    for tema, items in indice.items():
        print(f"  {tema}: {len(items)} imagenes")


if __name__ == "__main__":
    main()
