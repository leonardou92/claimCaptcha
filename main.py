"""Automatizador de captcha de selección de imágenes usando Selenium y Gemini."""

import os
import time
import base64
import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import hashlib
import threading
import io
from PIL import Image

import google.generativeai as genai
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

URL = "https://alpha123.uk/airdrop-sim2.html"

# Inicialización global del driver y wait (adaptado para webdriver-manager)
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
wait = WebDriverWait(driver, 20)

# --- FUNCIONES AUXILIARES ---
def get_image_url_from_style(style):
    try:
        # Busca url('...') o url("...") o url(...)
        m = re.search(r'url\((?:\'|\")?(.*?)(?:\'|\")?\)', style)
        if m and m.group(1):
            return m.group(1)
    except Exception:
        pass
    return None

def cache_get(h):
    try:
        with open('gemini_cache.json', 'r') as f:
            cache = json.load(f)
        return cache.get(h)
    except Exception:
        return None

def cache_set(h, ok):
    try:
        cache = {}
        try:
            with open('gemini_cache.json', 'r') as f:
                cache = json.load(f)
        except Exception:
            pass
        cache[h] = ok
        with open('gemini_cache.json', 'w') as f:
            json.dump(cache, f)
    except Exception:
        pass

def shrink_image_bytes(raw, max_dim=256):
    try:
        img = Image.open(io.BytesIO(raw))
        img.thumbnail((max_dim, max_dim))
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return buf.getvalue()
    except Exception:
        return raw

def consulta_gemini(img_b64, target_name, timeout=8):
    prompt = f"¿La imagen contiene un/una '{target_name}'? Responde solo 'sí' o 'no'."
    try:
        model = genai.GenerativeModel('gemini-pro-vision')
        resp = model.generate_content([
            prompt,
            {'mime_type': 'image/png', 'data': img_b64}
        ], generation_config={"temperature": 0.0}, safety_settings={})
        txt = resp.text.strip().lower()
        return 'sí' in txt or 'si' in txt
    except Exception:
        return False

def main():
    while True:
        now_str = time.strftime('%Y-%m-%d %H:%M:%S')
        print(f'\n==== Iteración captcha: {now_str} ====' )
        start_time = time.time()
        driver.get(URL)

        # Si aparece el modal 'Please try again later' o 'Too many people claiming, please retry' tras claimBtn, recargar
        try:
            error_msg_elem = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.ID, 'networkErrorMessage'))
            )
            error_msg = error_msg_elem.text.strip().lower()
            if (
                'please try again later' in error_msg or
                'too many people claiming, please retry' in error_msg
            ):
                print(f'Modal "{error_msg_elem.text.strip()}" detectado tras claim. Recargando para volver a intentar...')
                try:
                    now_click = time.strftime('%Y-%m-%d %H:%M:%S')
                    print(f'[{now_click}] Clic en networkErrorOk')
                    driver.find_element(By.ID, 'networkErrorOk').click()
                except Exception:
                    pass
                time.sleep(1)
                continue
        except Exception:
            pass

        # Espera y clic en claimBtn cuando esté activo (detectamos por outerHTML)
        for i in range(60):
            try:
                claim_btn = driver.find_element(By.ID, 'claimBtn')
                html = claim_btn.get_attribute('outerHTML')
                print(f'Intento {i+1}: {html}')
                classes = (claim_btn.get_attribute('class') or '')
                if 'display: inline-block' in html and 'active' in classes:
                    claim_btn.click()
                    print('Botón claimBtn clickeado.')
                    t_claim = time.time()
                    break
            except Exception:
                pass
            time.sleep(1)
        else:
            print('No se encontró claimBtn activo. Saliendo.')
            return

        # Clic en okConfirm
        wait.until(EC.element_to_be_clickable((By.ID, 'okConfirm')))
        driver.find_element(By.ID, 'okConfirm').click()

        # Espera por targetName (si existe) y por las celdas del grid
        try:
            WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.ID, 'targetName')))
        except Exception:
            pass

        # Intentamos esperar hasta que haya al menos una celda (timeout corto)
        try:
            cells = WebDriverWait(driver, 12).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#imageGrid .image-grid-cell'))
            )
        except Exception:
            # Fallback: intentar leer el grid si existe
            try:
                image_grid = driver.find_element(By.ID, 'imageGrid')
                cells = image_grid.find_elements(By.CLASS_NAME, 'image-grid-cell')
            except Exception:
                cells = []

        # Objetivo
        target_name = ''
        try:
            target_name = driver.find_element(By.ID, 'targetName').text.strip().lower()
        except Exception:
            target_name = ''

        print('Objeto objetivo:', target_name or '<vacío>')
        if not target_name:
            print('El objetivo está vacío después de claim. Recargando para volver a intentar...')
            time.sleep(1)
            continue
        print(f'Se encontraron {len(cells)} celdas en el grid')

        # Descargar imágenes y consultar IA en paralelo
        seleccionadas = 0
        future_to_cell = {}
        to_click = []
        session = requests.Session()
        with ThreadPoolExecutor(max_workers=16) as ex:
            for idx, cell in enumerate(cells):
                style = cell.get_attribute('style')
                img_url = get_image_url_from_style(style)
                if not img_url:
                    print(f'Celda {idx}: sin URL de imagen')
                    continue
                # Si la URL es relativa, la convertimos en absoluta
                if img_url.startswith('/'):
                    img_url = 'https://alpha123.uk' + img_url
                try:
                    r = session.get(img_url, timeout=10)
                    r.raise_for_status()
                    raw = r.content
                    h = hashlib.sha256(raw).hexdigest()
                    cached = cache_get(h)
                    data_is_target = (cell.get_attribute('data-is-target') or '').strip().lower()
                    if data_is_target in ('true', '1', 'yes'):
                        print(f'Celda {idx}: seleccionada por data-is-target (URL: {img_url})')
                        to_click.append((idx, cell))
                        seleccionadas += 1
                        continue
                    lower_url = img_url.lower()
                    if target_name and target_name in lower_url:
                        print(f'Celda {idx}: seleccionada por nombre en URL (URL: {img_url})')
                        to_click.append((idx, cell))
                        seleccionadas += 1
                        continue
                    if cached is not None:
                        print(f'Celda {idx}: cache Gemini = {cached} (URL: {img_url})')
                        if cached:
                            to_click.append((idx, cell))
                            seleccionadas += 1
                            continue
                        else:
                            continue
                    shrunk = shrink_image_bytes(raw, max_dim=256)
                    img_b64 = base64.b64encode(shrunk).decode('utf-8')
                    fut = ex.submit(consulta_gemini, img_b64, target_name, 3)  # timeout bajo para velocidad
                    future_to_cell[fut] = (idx, cell, h, img_url)
                except Exception as e:
                    print(f'Celda {idx}: error al descargar o procesar imagen: {e}')
            t_submit_done = time.time()
            for fut in as_completed(list(future_to_cell.keys())):
                entry = future_to_cell.get(fut)
                if not entry:
                    continue
                idx, cell, h, img_url = entry
                try:
                    ok = fut.result(timeout=3)
                    cache_set(h, ok)
                    print(f'Celda {idx}: Gemini={ok} (URL: {img_url})')
                    if ok:
                        to_click.append((idx, cell))
                        seleccionadas += 1
                except Exception as e:
                    print(f'Celda {idx}: DESCARTADA por timeout Gemini ({img_url})')
            t_gemini_end = time.time()

        t_before_clicks = time.time()
        try:
            elems = [cell for (_, cell) in to_click]
            if elems:
                driver.execute_script("for (let i=0;i<arguments[0].length;i++){arguments[0][i].click();}", elems)
        except Exception:
            for idx, cell in to_click:
                try:
                    cell.click()
                except Exception:
                    try:
                        driver.execute_script("arguments[0].click();", cell)
                    except Exception:
                        pass

        t_clicks_end = time.time()
        try:
            short_wait = WebDriverWait(driver, 2)
            short_wait.until(EC.presence_of_element_located((By.ID, 'verifyConfirm')))
            verify = driver.find_element(By.ID, 'verifyConfirm')
            try:
                verify.click()
            except Exception:
                try:
                    driver.execute_script("arguments[0].click();", verify)
                except Exception:
                    pass
        except Exception:
            pass

        t_verify_end = time.time()

        # Esperar resultado y mostrarlo
        try:
            # Esperar modal de error de servidor
            error_wait = WebDriverWait(driver, 6)
            error_title = error_wait.until(EC.presence_of_element_located((By.ID, 'networkErrorTitle')))
            error_text = error_title.text.strip()
            if 'Image Verification Server Error' in error_text:
                print('ERROR: Se detectó error de verificación. Recargando para reintentar...')
                try:
                    driver.find_element(By.ID, 'networkErrorOk').click()
                except Exception:
                    pass
                time.sleep(1)
                continue  # recargar y reintentar
        except Exception:
            pass

        # Esperar modal de verificación fallida
        try:
            verify_error_wait = WebDriverWait(driver, 6)
            verify_error_title = verify_error_wait.until(EC.presence_of_element_located((By.ID, 'verifyErrorTitle')))
            verify_error_text = verify_error_title.text.strip()
            if 'Verification Failed' in verify_error_text:
                print('ERROR: Verificación fallida. Recargando para reintentar...')
                try:
                    driver.find_element(By.ID, 'verifyErrorOk').click()
                except Exception:
                    pass
                time.sleep(1)
                continue  # recargar y reintentar
        except Exception:
            pass

        # Esperar resultado exitoso
        try:
            result_wait = WebDriverWait(driver, 10)
            result_wrap = result_wait.until(EC.presence_of_element_located((By.ID, 'scoreWrap')))
            score_title = driver.find_element(By.ID, 'scoreTitle').text.strip()
            score_time = driver.find_element(By.ID, 'scoreTime').text.strip()
            print(f'RESULTADO: {score_title} en {score_time} segundos')
        except Exception:
            print('No se detectó resultado automático en el DOM.')

        end_time = t_verify_end
        total = end_time - start_time
        print(f'Flujo finalizado. Seleccionadas: {seleccionadas}.')
        print('Tiempos (s): total=', round(total, 2))
        try:
            print(' - time to claim:', round(t_claim - start_time, 2))
        except Exception:
            pass
        try:
            print(' - time clicks:', round(t_clicks_end - t_before_clicks, 2))
        except Exception:
            pass
        try:
            print(' - time verify:', round(t_verify_end - t_clicks_end, 2))
        except Exception:
            pass

        print('El navegador queda abierto para inspección. Presiona Enter para cerrar.')
        try:
            input()
        except Exception:
            pass
        break
    # info mínima
    print('Objeto objetivo:', target_name or '<vacío>')
    print(f'Se encontraron {len(cells)} celdas en el grid')

    # Descargar imágenes y consultar IA en paralelo
    seleccionadas = 0
    future_to_cell = {}
    to_click = []  # lista de (idx, WebElement) que validamos para clicar
    session = requests.Session()  # reutiliza conexiones
    # Aumentamos workers para paralelizar más (ajusta según cuota de Gemini)
    download_start = time.time()
    with ThreadPoolExecutor(max_workers=16) as ex:
        for idx, cell in enumerate(cells):
            style = cell.get_attribute('style')
            img_url = get_image_url_from_style(style)
            if not img_url:
                continue
            try:
                r = session.get(img_url, timeout=10)
                r.raise_for_status()
                raw = r.content
                h = hashlib.sha256(raw).hexdigest()
                cached = cache_get(h)
                # Prefiltrado rápido: si el DOM marca la celda como objetivo, seleccionamos
                data_is_target = (cell.get_attribute('data-is-target') or '').strip().lower()
                if data_is_target in ('true', '1', 'yes'):
                    to_click.append((idx, cell))
                    seleccionadas += 1
                    continue
                # Prefiltrado por URL (nombre de archivo contiene target)
                lower_url = img_url.lower()
                if target_name and target_name in lower_url:
                    to_click.append((idx, cell))
                    seleccionadas += 1
                    continue
                if cached is not None:
                    if cached:
                        to_click.append((idx, cell))
                        seleccionadas += 1
                        continue
                    else:
                        continue
                shrunk = shrink_image_bytes(raw, max_dim=256)
                img_b64 = base64.b64encode(shrunk).decode('utf-8')
                fut = ex.submit(consulta_gemini, img_b64, target_name, 8)
                future_to_cell[fut] = (idx, cell, h)
            except Exception:
                pass
        t_submit_done = time.time()
        for fut in as_completed(list(future_to_cell.keys())):
            entry = future_to_cell.get(fut)
            if not entry:
                continue
            idx, cell, h = entry
            try:
                ok = fut.result()
                cache_set(h, ok)
                if ok:
                    to_click.append((idx, cell))
                    seleccionadas += 1
            except Exception:
                pass
        t_gemini_end = time.time()
    # Ahora clicar todas las celdas validadas en bloque usando JS (más rápido)
    t_before_clicks = time.time()
    try:
        elems = [cell for (_, cell) in to_click]
        if elems:
            driver.execute_script("for (let i=0;i<arguments[0].length;i++){arguments[0][i].click();}", elems)
    except Exception:
        # fallback: intentar clicks individuales si JS falla
        for idx, cell in to_click:
            try:
                cell.click()
            except Exception:
                try:
                    driver.execute_script("arguments[0].click();", cell)
                except Exception:
                    pass

    t_clicks_end = time.time()
    # Clic en Verify (usar JS como método rápido/fallback)
    try:
        short_wait = WebDriverWait(driver, 2)
        short_wait.until(EC.presence_of_element_located((By.ID, 'verifyConfirm')))
        verify = driver.find_element(By.ID, 'verifyConfirm')
        try:
            verify.click()
        except Exception:
            try:
                driver.execute_script("arguments[0].click();", verify)
            except Exception:
                pass
    except Exception:
        pass

    # Esperar resultado y mostrarlo
    try:
        result_wait = WebDriverWait(driver, 10)
        result_wrap = result_wait.until(EC.presence_of_element_located((By.ID, 'scoreWrap')))
        score_title = driver.find_element(By.ID, 'scoreTitle').text.strip()
        score_time = driver.find_element(By.ID, 'scoreTime').text.strip()
        print(f'RESULTADO: {score_title} en {score_time} segundos')
    except Exception:
        print('No se detectó resultado automático en el DOM.')
    t_verify_end = time.time()

    # Mostrar métricas por etapas (si existen las marcas temporales)
    end_time = t_verify_end
    total = end_time - start_time
    print(f'Flujo finalizado. Seleccionadas: {seleccionadas}.')
    print('Tiempos (s): total=', round(total, 2))
    try:
        print(' - time to claim:', round(t_claim - start_time, 2))
    except Exception:
        pass
    # Solo métricas locales
    try:
        print(' - time clicks:', round(t_clicks_end - t_before_clicks, 2))
    except Exception:
        pass
    try:
        print(' - time verify:', round(t_verify_end - t_clicks_end, 2))
    except Exception:
        pass

    # Dejar el navegador abierto para inspección manual
    print('El navegador queda abierto para inspección. Presiona Enter para cerrar.')
    try:
        input()
    except Exception:
        pass


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('Error principal:', e)
    finally:
        try:
            driver.quit()
        except Exception:
            pass
