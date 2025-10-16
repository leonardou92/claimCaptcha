
# Resolver captcha de imágenes con IA (Gemini)

Este proyecto automatiza la resolución de captchas de selección de imágenes en una página web usando Selenium y Gemini (Google Generative AI).

## Características
- Automatización completa con Selenium (Chrome)
- Reconocimiento de imágenes usando Gemini (google-generativeai)
- Prefiltrado rápido por nombre de archivo y caché local para máxima velocidad
- Manejo automático de modales de error y recarga
- El navegador permanece abierto al finalizar para inspección manual
- Logs detallados de cada acción

## Requisitos
- Python 3.12+
- Google Chrome instalado
- Clave de API de Gemini (Google Generative AI)

## Instalación
1. Clona el repositorio o copia los archivos en tu máquina.
2. Crea y activa un entorno virtual (opcional pero recomendado):



  ===============================
  Variables de entorno
  ===============================

  # URL de la página principal donde está el captcha
  TARGET_URL=https://tupagina.com/captcha

  # Clave de API de Gemini (obligatoria)
  GEMINI_API_KEY=tu_api_key_aqui

  # Palabra objetivo del captcha (opcional, si se deja vacío se detecta automáticamente)
  TARGET_NAME=


  **Resolución de URLs de imágenes:**
  - Si la celda contiene una imagen `<img src="...">`, se usará ese src tal cual (absoluto o relativo, como lo entrega el HTML).
  - Si no, se extraerá la URL del style/background y se resolverá como absoluta respecto a la página principal.
```
TARGET_URL=https://tupagina.com/captcha         # URL de la página principal donde está el captcha
IMG_BASE_URL=https://tupagina.com               # (opcional) Base global para las imágenes, por defecto igual a TARGET_URL
IMG_BASE_URL_IMAGEGRID=https://imagenes.com     # (opcional) Base específica para imágenes del contenedor con id="imageGrid"
GEMINI_API_KEY=tu_api_key_aqui                 # Tu clave de Gemini
TARGET_NAME=perro                              # (opcional) Objetivo del captcha, si se deja vacío se detecta automáticamente
```


**Resolución de URLs de imágenes:**
- Si la celda contiene una imagen `<img src="...">`, se usará ese src tal cual (absoluto o relativo).
- Si no, se extraerá la URL del style/background y se resolverá así:
  1. Si el contenedor padre de la imagen tiene `data-base-url`, se usa ese valor como base.
  2. Si existe una variable de entorno `IMG_BASE_URL_<IDCONTENEDOR>`, se usa como base (por ejemplo, `IMG_BASE_URL_IMAGEGRID`).
  3. Si no, se usa `IMG_BASE_URL` o `TARGET_URL` como fallback.

## Uso
Ejecuta el script principal:
```bash
python main.py
```
El navegador se abrirá y resolverá el captcha automáticamente. Al finalizar, quedará abierto para inspección manual (presiona Enter para cerrar).

### Modo headless (opcional)
Puedes activar el modo headless editando el script y agregando la opción correspondiente en la configuración de Selenium.

## Notas importantes
- El script detecta y recarga automáticamente si aparecen los modales de error "Please try again later", "Too many people claiming, please retry" o "Image Verification Server Error" tras claimBtn.
- Si el captcha no aparece tras claimBtn, también recarga automáticamente.
- El uso de Gemini tiene límites de cuota y velocidad. El script usa caché y paraleliza consultas para minimizar el consumo.
- Puedes ajustar el número de workers y el prompt de Gemini en el código para optimizar velocidad y precisión.

## Estructura
- main.py: Script principal y lógica completa
- requirements.txt: Dependencias
- gemini_cache.json: Caché local de respuestas de Gemini

---
Desarrollado por GitHub Copilot.
