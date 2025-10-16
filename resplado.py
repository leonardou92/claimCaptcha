
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import time

URL = 'https://alpha123.uk/airdrop-sim2.html'

# Inicializa el navegador

options = webdriver.ChromeOptions()
 # options.add_argument('--headless')  # Quita esto si quieres ver el navegador
options.add_argument('--no-sandbox')

from selenium.webdriver.chrome.service import Service
driver_path = ChromeDriverManager().install()
service = Service(driver_path)
driver = webdriver.Chrome(service=service, options=options)
driver.get(URL)
wait = WebDriverWait(driver, 30)

# Espera a que claimBtn esté visible

# Depuración visual: espera y muestra el estado del botón
for i in range(30):
    claim_btn = driver.find_element(By.ID, 'claimBtn')
    html = claim_btn.get_attribute('outerHTML')
    print(f'Intento {i+1}')
    if 'display: inline-block' in html and 'active' in claim_btn.get_attribute('class'):
        claim_btn.click()
        print('Botón claimBtn clickeado.')
        break
    time.sleep(1)
else:
    print('No se encontró claimBtn con display: inline-block')
    driver.quit()
    exit(1)

# Espera y haz clic en okConfirm
wait.until(EC.element_to_be_clickable((By.ID, 'okConfirm')))
driver.find_element(By.ID, 'okConfirm').click()

# Espera a que aparezca el captcha
wait.until(EC.presence_of_element_located((By.ID, 'imageGrid')))
image_grid = driver.find_element(By.ID, 'imageGrid')


# Automatización de selección de imágenes
target_name = driver.find_element(By.ID, 'targetName').text.strip().lower()
print(f'Objeto objetivo: {target_name}')

cells = image_grid.find_elements(By.CLASS_NAME, 'image-grid-cell')
seleccionadas = 0
for idx, cell in enumerate(cells):
    style = cell.get_attribute('style')
    print(f'Celda {idx}: style={style}')
    if f"{target_name}.png" in style:
        cell.click()
        seleccionadas += 1
        print(f'Celda {idx} seleccionada.')
print(f'Total seleccionadas: {seleccionadas}')

# Haz clic en verifyConfirm
wait.until(EC.element_to_be_clickable((By.ID, 'verifyConfirm')))
driver.find_element(By.ID, 'verifyConfirm').click()

# Espera y haz clic en verifyConfirm
wait.until(EC.element_to_be_clickable((By.ID, 'verifyConfirm')))
driver.find_element(By.ID, 'verifyConfirm').click()

print('Captcha procesado y verificado.')
input('Presiona Enter para cerrar el navegador...')
# driver.quit()  # No cerrar el navegador para inspección manual
