from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import ProcessPoolExecutor
import concurrent.futures
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from . import parseFunctions as ps
import pandas as pd
import os

# Mozilla Firefox
# driver_path = 'path/to/geckodriver.exe'
# driver_options = webdriver.FirefoxOptions()
# driver_options.add_argument(f'--webdriver.gecko.driver={driver_path}')

# VARIABLES
NUM_THREADS = 15
COUNT_SUCCESS = 0
COUNT_ERROR = 0
NUM_TOTAL_REQUESTS = 100
ALERT = 0
captchas = []



def WebScrapingPoderJudicial(identificador, exp_cod, socketio):
    cod_expediente, cod_anio, cod_incidente, cod_distprov, cod_organo, cod_especialidad, cod_instancia = exp_cod.split('-')
    
    global COUNT_SUCCESS, COUNT_ERROR,ALERT
    print("Starting..." + str(identificador) + " - " + time.strftime("%H:%M:%S"))
    driver = None
    try:
        # service = Service(executable_path="/usr/bin/chromedriver")
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        download_path = os.path.join(os.getcwd(), "exp", "files")
        chrome_options.add_experimental_option('prefs', {
            'download.default_directory': download_path,
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
            'safebrowsing.enabled': True,
        })

        # driver = webdriver.Chrome(service=service, options=chrome_options)
        driver = webdriver.Chrome(options=chrome_options)      
        driver.set_page_load_timeout(30)

        driver.get("https://cej.pj.gob.pe/cej/forms/busquedaform.html")

        buttonSound = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.ID, "btnRepro"))
        )
        buttonSound.click()

        ul_element = WebDriverWait(driver, 2).until(
            EC.visibility_of_element_located((By.ID, "divTabs"))
        )
        second_li_element = ul_element.find_elements(By.TAG_NAME, "li")[1]
        second_li_element.click()

        inputExpedient = WebDriverWait(driver, 3).until(
            EC.visibility_of_element_located((By.ID, "cod_expediente"))
        )
        inputExpedient.send_keys(cod_expediente)   # 00001
        inputExpedient = driver.find_element(By.ID, "cod_anio")
        inputExpedient.send_keys(cod_anio)    # 2005
        inputExpedient = driver.find_element(By.ID, "cod_incidente")
        inputExpedient.send_keys(cod_incidente)   # 0
        inputExpedient = driver.find_element(By.ID, "cod_distprov")
        inputExpedient.send_keys(cod_distprov)    # 1817
        inputExpedient = driver.find_element(By.ID, "cod_organo")
        inputExpedient.send_keys(cod_organo)  # JR
        inputExpedient = driver.find_element(By.ID, "cod_especialidad")
        inputExpedient.send_keys(cod_especialidad)  # CO
        inputExpedient = driver.find_element(By.ID, "cod_instancia")
        inputExpedient.send_keys(cod_instancia)  # 06

        elementSound = driver.find_element(By.ID, "1zirobotz0")
        elementSound_value = elementSound.get_attribute("value")
        # Perform other actions as needed
        inputExpedient = driver.find_element(By.ID, "codigoCaptcha")
        inputExpedient.send_keys(elementSound_value)
        captchas.append(elementSound_value)
        buttonGetExpedient = driver.find_element(By.ID, "consultarExpedientes")
        buttonGetExpedient.click()
        error_count = 0

        # Agregar un bucle para intentar encontrar el elemento 'command' hasta 3 intentos
        for _ in range(3):
            try:
                formExpedient = driver.find_element(By.ID, "command")
                buttons = formExpedient.find_elements(By.TAG_NAME, "button")
                if buttons:
                    buttons[0].click()
                
                break # Salir del bucle si el elemento se encuentra y se hace clic con éxito
            except NoSuchElementException:
                # Incrementar el contador de errores
                error_count += 1

                time.sleep(0.5)  # Esperar un segundo antes de intentar nuevamente

        # Contar el error solo si no se encontró el elemento después de los 3 intentos
        if error_count == 3:
            COUNT_ERROR += 1
            print(
                f"Error {identificador}: No se encontró el elemento 'command' después de {error_count} intentos"
            )
        else:  
            reporte_expediente = driver.find_element(By.ID,"gridRE").get_attribute("outerHTML")
            partes_procesales = driver.find_element(By.ID,"collapseTwo").get_attribute("outerHTML")
            seguimiento_expediente = driver.find_element(By.ID,"collapseThree").get_attribute("outerHTML")
            reporte_html = [reporte_expediente, partes_procesales, seguimiento_expediente]

            expediente = ps.extract_expediente_info(reporte_html, "exp"+str(identificador), driver)
            
            COUNT_SUCCESS += 1
    except Exception as e:
        print("Error " + str(identificador) + " : " + str(e))
        COUNT_ERROR += 1
    finally:
        if driver:
            driver.quit()

    progress_percentage = ((COUNT_ERROR+COUNT_SUCCESS)) / NUM_TOTAL_REQUESTS * 100
    socketio.emit("progress_update", {"percentage": progress_percentage })
    if (COUNT_ERROR+COUNT_SUCCESS) % ALERT == 0:
      socketio.emit("console_output", {"message": f"solicitudes procesadas {str((COUNT_ERROR+COUNT_SUCCESS))}"+"\n" })
    print("Finished..." + str(identificador) + " - " + time.strftime("%H:%M:%S"))


def executeWebScraping(requests, threads,alert,socketio):
    expedientes_excel = pd.read_excel(requests)
    expedientes_df = pd.DataFrame(expedientes_excel)
    columna_exp = expedientes_df['No. Expediente']
    cods_exp = [exp for exp in columna_exp]
    
    global NUM_THREADS, NUM_TOTAL_REQUESTS,ALERT
    NUM_THREADS = int(threads)
    NUM_TOTAL_REQUESTS = len(cods_exp)
    ALERT = int(alert)
    CODIGOS = cods_exp
    
    inicio = time.localtime()
    
    # with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        futures = [
            executor.submit(WebScrapingPoderJudicial, i, CODIGOS[i],socketio)
            for i in range(NUM_TOTAL_REQUESTS)
        ]
        for future in concurrent.futures.as_completed(futures):
            future.result()
            
    fin = time.localtime()
    print("Inicio de la ejecución" + time.strftime("%H:%M:%S",inicio))
    print("Fin de la ejecución" + time.strftime("%H:%M:%S",fin))
    print("Success: " + str(COUNT_SUCCESS))
    print("Error: " + str(COUNT_ERROR))

    

    