
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
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```
3. Instala las dependencias:
  ```bash
  pip install -r requirements.txt
  ```

## Variables de entorno
Debes definir la clave de Gemini en tu entorno:
```bash
export GEMINI_API_KEY="tu_clave_de_gemini"
```

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
