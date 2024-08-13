import pandas as pd
import random
import time
from parsel import Selector
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
import undetected_chromedriver as uc
#Lo que sigue es nuevo
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import unicodedata

# Función para normalizar texto
def normalizar(texto):
    return unicodedata.normalize('NFD', str(texto)).encode('ascii', 'ignore').decode('utf-8')

# Inicializamos el driver
options = webdriver.ChromeOptions()
options.add_argument('--start-maximized')
options.add_argument('--disable-extensions')
service = Service(executable_path='chromedriver-win64\\chromedriver.exe')
driver = webdriver.Chrome(service=service, options=options)

# Accedemos al link
driver.get('https://www.casaley.com.mx/nuestras-tiendas-2/')
time.sleep(3)

# Obtener todas las pestañas
tabs = driver.find_elements(By.XPATH, '//li[contains(@class, "r-tabs-tab")]/a')

nombres = []
direcciones = []
telefonos = []

# Iterar sobre cada pestaña y hacer clic
for tab in tabs:
    tab.click()
    time.sleep(2)  # Esperar a que la pestaña cargue

    # Extraer los elementos de nombres y direcciones
    nombres_elems = driver.find_elements(By.XPATH, '//h5[@class="elementor-image-box-title"]')
    direcciones_elems = driver.find_elements(By.XPATH, '//p[@class="elementor-image-box-description"]')

    # Iterar sobre los elementos y extraer el texto
    for i in range(len(nombres_elems)):
        # Limpieza
        nombre_aux = normalizar(nombres_elems[i].text)
        nombres.append(nombre_aux)

        direcciones_aux = normalizar(direcciones_elems[i].text)
        direcciones_aux = direcciones_aux.split('\n')
        direcciones.append(direcciones_aux[0])

        # Verificar si hay al menos 3 elementos en direcciones_aux
        if len(direcciones_aux) > 2:
            telefonos.append(direcciones_aux[2])
        else:
            telefonos.append('')

# Crear el DataFrame con los datos extraídos
data = {
    'Nombre de tienda': nombres,
    'Direccion': direcciones,
    'Telefono': telefonos
}

df = pd.DataFrame(data)
df.to_excel('Tiendas_Ley.xlsx', index=False)

# Mostrar el DataFrame resultante
print(df)

# Cerrar el driver
driver.quit()