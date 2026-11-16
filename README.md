# Maduro Livre — bot de Telegram

Bot de sátira política antichavista en Telegram, con dos caras:

- **Lex**, el alter ego del bot: conversa con humor sarcástico, responde siempre
  en 5 líneas y remata con una imagen satírica sobre Maduro, Cilia Flores o las
  comunas (imágenes libres de Wikimedia Commons).
- **El Morral Digital**: integra el catálogo de libros del sitio
  [El Morral Digital](https://1956jp.github.io/morral-digital/) — los usuarios
  pueden explorar la biblioteca, leer gratis los textos de enlace libre y
  reclamar las descargas de los títulos de pago desde el propio chat.
- **Recordatorios persistentes**: crea avisos con `/recordar`; el formato
  clásico se parsea sin IA y los pedidos en lenguaje libre los interpreta
  Lex, que "predice" el asunto y los minutos que faltan. Sobreviven reinicios
  (SQLite) y se reprograman al arrancar.

## Comandos

| Comando | Qué hace |
|---|---|
| `/start` | Saludo inicial y resumen de capacidades |
| `/ayuda` | Lista completa de comandos y usos |
| `/libros` | Menú del catálogo: todas las obras o filtrar por corriente |
| `/leer` | Solo las obras de lectura gratuita |
| `/descargar` | Reclamar la descarga de un título de pago (requiere pedido `paid` en la tienda) |
| `/recordar <mensaje> <n> <min\|horas\|dias>` | Crea un recordatorio (ej.: `/recordar Comprar pan 30 minutos`) |
| `/recordar <mensaje libre>` | Lex interpreta cuándo avisarte (ej.: `/recordar reunion manana 9am`) |
| `/lista` / `/borrar <#>` | Ver los recordatorios pendientes / cancelar uno |
| `/image [tema]` | Publica una imagen satírica sobre un tema |

Además responde a cualquier mensaje con la voz de Lex (LLM), y publica imágenes
en horarios programados.

## Instalación

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
cp .env.example .env      # y rellena tus valores reales
venv/bin/python descargar_imagenes.py   # baja las imágenes (libres, con créditos)
venv/bin/python bot.py
```

Requiere Python 3.10+.

## Configuración (`.env`)

| Variable | Descripción |
|---|---|
| `TELEGRAM_TOKEN` | Token del bot (lo da [@BotFather](https://t.me/BotFather)) |
| `API_BASE_URL` | Endpoint OpenAI-compatible del proveedor LLM |
| `API_KEY` | Clave del proveedor |
| `MODEL` | Modelo a usar |
| `CONTEXTO_PATH` | (opcional) Ruta alternativa al prompt de Lex (`contexto.txt`) |
| `IMAGENES_DIR` | (opcional) Carpeta de imágenes (por defecto `imagenes/`) |
| `IMAGEN_ORDEN` | (opcional) Orden de publicación de temas |

El LLM es **agnóstico**: cualquier endpoint compatible con la API de OpenAI
sirve. Ejemplos probados: **Groq** (free, `https://api.groq.com/openai/v1`),
**OpenRouter** y **Ollama local** (100 % gratis, sin clave real):
`API_BASE_URL=http://localhost:11434/v1` con `API_KEY=ollama`.

Si usas Ollama y Lex se cuelga (runner atascado con la CPU al límite),
descarga el modelo y reintenta:

```bash
./reparar_ollama.sh
```

## Estructura

```
bot.py                  bot completo (single-file)
contexto.txt            prompt/personalidad de Lex
descargar_imagenes.py   descarga imágenes libres de Wikimedia Commons
imagenes/<tema>/        imágenes + creditos.txt por tema
reparar_ollama.sh       recuperación del runner de Ollama atascado
.env.example            plantilla de configuración (el .env real NO se sube)
```

## Notas

- Las imágenes proceden de Wikimedia Commons con licencias libres (PD/CC0/CC BY/CC BY-SA); los créditos por imagen están en `imagenes/<tema>/creditos.txt`.
- Los recordatorios se guardan en `~/.local/share/maduro_bot/recordatorios.db`; al arrancar, el bot reprograma los pendientes y descarta los vencidos.
- Sátira política sobre figuras públicas: el bot no representa ni se hace pasar por persona real.
- Integración con El Morral Digital: consulta el catálogo público del sitio (con respaldo local) y la entrega de títulos de pago se realiza mediante URLs firmadas de la Edge Function de Supabase, solo tras verificar el pedido.
- No subas nunca `.env` (contiene tu token y claves). El `.gitignore` lo bloquea.
