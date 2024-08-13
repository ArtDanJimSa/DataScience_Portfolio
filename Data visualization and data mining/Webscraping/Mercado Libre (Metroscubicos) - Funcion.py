# Importación de libreria utilizadas

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
import unicodedata
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import Label
from tkinter import Label, Entry, Text, Button, StringVar
import re
import requests
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import math

##################################################################################
#                                                                                #
#  Webscraping de metroscubicos.com - mercado libre                              #
#                                                                                #
##################################################################################

####################             Función de limpieza             ####################  

# limpieza del formato
def normalizar(texto):
    return unicodedata.normalize('NFD', str(texto)).encode('ascii', 'ignore').decode('utf-8')

def procesar_datos_csv(df_original):
    # Función para clasificar tipo de operación (venta/renta) y tipo de propiedad (nave/terreno/bodega)
    def clasificar_propiedad(titulo):
        tipo_propiedad = ""
        # Verificar si es Terreno, Nave o Bodega
        if re.search(r'\b(Departamento[s]?|DEPARTAMENTO)\b', titulo, re.IGNORECASE):
            tipo_propiedad += "Departamento,"
        if re.search(r'\b(Casa[s]?|Duplex)\b', titulo, re.IGNORECASE):
            tipo_propiedad += "Casa,"
        if not tipo_propiedad:
            tipo_propiedad += "No especificado"  # Si no encuentra ninguna opción, se establece como "No especificado"    
        return tipo_propiedad.rstrip(',')  # Eliminar la última coma si está presente
    
    # Filtrar los datos para obtener vivanuncios e inmuebles24
    df_viva = df_original[df_original['ID'].str.startswith('VIVA')]
    df_inmu = df_original[df_original['ID'].str.startswith('INMU')]
    
    # Eliminar duplicados de vivanuncios que también están en inmuebles24
    df_viva_sin_duplicados = df_viva[~df_viva['Nombre'].isin(df_inmu['Nombre'])]

    # Añadir tipo de propiedad utilizando .loc
    df_viva_sin_duplicados.loc[:, 'TipoPropiedad'] = df_viva_sin_duplicados['Nombre'].apply(lambda x: pd.Series(clasificar_propiedad(x)))

    df_viva_sin_duplicados = df_viva_sin_duplicados[['ID', 'Nombre', 'Direccion', 'Precio', 'Operacion', 'TipoPropiedad', 'Area terreno', 
                                           'Superficie Construida', 'Banos', 'Medios banos', 'Recamaras', 'Estacionamientos', 
                                           'Edad', 'Piso', 'Alberca', 'Cocina integral', 'Amueblado', 'Elevador', 'Aire acondicionado', 'Terraza', 'URL']]

    # Añadir los datos de las otras páginas
    df_others = df_original[~df_original['ID'].str.startswith(('VIVA', 'INMU'))]
    df_resultado = pd.concat([df_viva_sin_duplicados, df_inmu, df_others])

    return df_resultado

def obtener_tipo_cambio(moneda_origen, moneda_destino):
    # Leer el archivo de texto
    with open("images/tipo_cambio.txt", "r") as file:
        lines = file.readlines()
    
    # Filtrar el tipo de cambio específico
    for line in lines[1:]:  # Saltar la primera línea que contiene los encabezados
        moneda_orig, moneda_dest, tipo_cambio = line.strip().split(", ")
        if moneda_orig == moneda_origen and moneda_dest == moneda_destino:
            return float(tipo_cambio)
    
    return None  # Retornar None si no se encuentra el tipo de cambio

# Resto del código sin cambios
def dolares_a_pesos(dolares, tipo_cambio):
    pesos = dolares * tipo_cambio
    return pesos

####################             Funciones de webscraping             ####################                    


def Webscraping_metroscubicos(link, busqueda_ini):
    # Configuración del navegador
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_argument('--disable-extensions')
    service = Service(executable_path='chromedriver-win64\\chromedriver.exe')
    driver = webdriver.Chrome(service=service, options=options)

    # Navegación a la página principal
    driver.get(link)
    print('Page Loaded Successfully')
    lnks = []

    # Obteniendo enlaces de los desarrollos
    #urls = driver.find_elements(By.XPATH, '//div[@class="ui-search-item_groupelement ui-search-item_title-grid"]/a')
    urls = driver.find_elements(By.XPATH, '//div[@class="andes-card ui-search-result ui-search-result--res andes-card--flat andes-card--padding-16 andes-card--animated"]/div[2]/div/div[1]/div/a')
    for url in urls:
        all_links = url.get_attribute("href")
        lnks.append(all_links)
    #print(lnks)

    # Iterando sobre las páginas siguientes (máximo 200)
    for i in range(200):
        if i < 200:
            try:
                if busqueda_ini < 48:
                    break
                siguiente = driver.find_element(By.XPATH, '//li[@class="andes-pagination__button andes-pagination__button--next"]/a').get_attribute("href")
                driver.get(siguiente)
                sleep(1)
                urls2 = driver.find_elements(By.XPATH, '//div[@class="ui-search-item__group__element ui-search-item__title-grid"]/a')
                for url in urls2:
                    all_links2 = url.get_attribute("href")
                    lnks.append(all_links2)
            except:
                pass
    #print(lnks)

    # Limitando la cantidad de enlaces
    if len(lnks) > busqueda_ini:
        lnks = lnks[:busqueda_ini]
    
    #driver.quit()

    all_data = []
    for links in lnks:
        #driver = webdriver.Chrome(service=service, options=options)
        driver.get(links)
        time.sleep(random.randint(1, 5))
        try:
            # Extrayendo información de la propiedad
            property_name = driver.find_element(By.XPATH, '//div[@class="ui-pdp-header__title-container"]/h1')
            name = property_name.text
            name = normalizar(name)

            property_precio = driver.find_element(By.XPATH, '//span[@class="andes-money-amount__fraction"]')
            precio = property_precio.text
            precio = normalizar(precio)

            # Condicionales para los precios
            if "MN" in precio:
                precio = int(precio.replace("MN ", "").replace(",", ""))
            if "USD" in precio:
                if "/mes" in precio:
                    precio = float(precio.replace("$", "").replace(",", ".").replace("USD ", "").replace("/mes", ""))
                    tipo_cambio_usd_mxn = obtener_tipo_cambio('USD', 'MXN')
                    precio = dolares_a_pesos(precio, tipo_cambio_usd_mxn)
                else:
                    precio = float(precio.replace("$", "").replace(",", ".").replace(" USD", ""))
                    tipo_cambio_usd_mxn = obtener_tipo_cambio('USD', 'MXN')
                    precio = dolares_a_pesos(precio, tipo_cambio_usd_mxn)
        except:
            pass

        try:
            # Extrayendo direccion
            property_direccion = driver.find_element(By.XPATH, '//*[@id="location"]/div/div[1]/div/p')
            direccion = property_direccion.text
            direccion = normalizar(direccion)
        except:
            continue

        # Extraemos el tipo de operación y el ID
        try:
            property_operacion = driver.find_element(By.XPATH, '//div[@class="ui-pdp-container__row ui-pdp-container__row--header"]/div/div[1]/span')
            operacion_ = property_operacion.text
            operacion_ = normalizar(operacion_)

            patron = r"\b(Venta|Renta)\b"
            resultado = re.search(patron, operacion_)
            if resultado:
                operacion_ = resultado.group()
            if operacion_ == 'Venta':
                operacion = 'venta'
            if operacion_ == 'Renta':
                operacion = 'renta'
        except:
            pass

        # Obtenemos el ID
        try:
            patron = r"MLM-\d+"
            resultado = re.search(patron, links)
            if resultado:
                ID = resultado.group()
            ID = "M" +  str(ID)
            #print(ID)
        except:
            pass


        detalles = {}
        for i in range(1, 8):
            try:
                nombre_Caracteristica = driver.find_element(By.XPATH, f'//div[@class="ui-pdp-container__row ui-pdp-container__row--highlighted-specs-res"]/div/div[{i}]/span').text
                nombre_Caracteristica = normalizar(nombre_Caracteristica)
                valor = int(''.join(filter(str.isdigit, nombre_Caracteristica)))
                # Lógica para agrupar en las columnas según su tipo
                if 'terreno' in nombre_Caracteristica:
                    detalles['Area terreno'] = valor
                elif 'totales' in nombre_Caracteristica:
                    valor_terreno = nombre_Caracteristica.split()[0]
                    detalles['Superficie Construida'] = valor_terreno
                elif 'banos' in nombre_Caracteristica:
                    detalles['Baños'] = valor
                elif 'bano' in nombre_Caracteristica:
                    detalles['Baños'] = valor
                elif 'recamaras' in nombre_Caracteristica:
                    detalles['Recamaras'] = valor
                elif 'recamara' in nombre_Caracteristica:
                    detalles['Recamaras'] = valor
                elif 'Estacionamientos' in nombre_Caracteristica:
                    detalles['Estacionamientos'] = valor
                elif 'Antiguedad' in nombre_Caracteristica:
                    detalles['Edad'] = valor
            except:
                pass

        # --------------------------------------------
        # Caracteristicas
        #print(name)

        caracteristicas = {
            'Piso': 0,
            'Mascotas': 0,
            'Alberca': 0,
            'Jacuzzi': 0,
            'Cocina integral': 0,
            'Acceso discapacitados': 0,
            'Amueblado': 0,
            'Elevador': 0,
            'Caseta de guardia': 0,
            'Cuartos de servicio':0,
            'Acceso discapacitados': 0,
            'Frente a Parque': 0,
            'Aire acondicionado': 0,
            'Gimnasio': 0,
            'Terraza': 0,
            'Seguridad privada': 0
        }

        for i in range(1, 3):
            for j in range(1, 8):
                try:
                    nombre_caracteristicas = driver.find_element(By.XPATH, f'//div[@class="ui-vpp-highlighted-specs__attribute-columns"]/div[{i}]/div[{j}]/div/div[2]/p/span[1]').text
                    valor_caracteristicas = driver.find_element(By.XPATH, f'//div[@class="ui-vpp-highlighted-specs__attribute-columns"]/div[{i}]/div[{j}]/div/div[2]/p/span[2]').text
                    nombre_caracteristicas = normalizar(nombre_caracteristicas)
                    valor_caracteristicas = normalizar(valor_caracteristicas)
                    #print(nombre_caracteristicas)
                    #print(valor_caracteristicas)
                    if 'Numero de piso de la unidad' in nombre_caracteristicas:
                        caracteristicas['Piso'] = int(valor_caracteristicas)
                    if 'Admite mascotas' in nombre_caracteristicas:
                        if valor_caracteristicas=='Si':
                            caracteristicas['Mascotas'] = 1
                    if 'Alberca' in nombre_caracteristicas:
                        if valor_caracteristicas=='Si':
                            caracteristicas['Alberca'] = 1
                    if 'Jacuzzi' in nombre_caracteristicas:
                        if valor_caracteristicas=='Si':
                            caracteristicas['Jacuzzi'] = 1
                    if 'Cocina integral' in nombre_caracteristicas:
                        if valor_caracteristicas=='Si':
                            caracteristicas['Cocina integral'] = 1
                    if 'Acceso discapacitados' in nombre_caracteristicas:
                        if valor_caracteristicas=='Si':
                            caracteristicas['Acceso discapacitados'] = 1
                    if 'Amueblado' in nombre_caracteristicas:
                        if valor_caracteristicas=='Si':
                            caracteristicas['Amueblado'] = 1
                    if 'Ascensor' in nombre_caracteristicas:
                        if valor_caracteristicas=='Si':
                            caracteristicas['Elevador'] = 1
                    if 'Caseta de guardia' in nombre_caracteristicas:
                        if valor_caracteristicas=='Si':
                            caracteristicas['Caseta de guardia'] = 1
                    if 'Cuartos de servicio' in nombre_caracteristicas:
                        if valor_caracteristicas=='Si':
                            caracteristicas['Cuartos de servicio'] = 1
                    if 'Acceso discapacitados' in nombre_caracteristicas:
                        if valor_caracteristicas=='Si':
                            caracteristicas['Acceso discapacitados'] = 1                                           
                    if 'Terraza' in nombre_caracteristicas:
                        if valor_caracteristicas=='Si':
                            caracteristicas['Terraza'] = 1 
                    if 'Estacionamientos' in nombre_caracteristicas:
                        valor = int(''.join(filter(str.isdigit, valor_caracteristicas)))
                        detalles['Estacionamientos'] = valor   
                    if 'Antiguedad' in nombre_caracteristicas:
                        valor = int(''.join(filter(str.isdigit, valor_caracteristicas)))
                        detalles['Edad'] = valor
                except:
                    pass

        data = {
            'ID': ID,
            'Nombre': name,
            'Direccion': direccion,
            'Precio': precio,
            'Operacion': operacion,
            'Area terreno': detalles.get('Area terreno', ''),
            'Superficie Construida': detalles.get('Superficie Construida', ''),
            'Banos': detalles.get('Baños', ''),
            'Medios banos': detalles.get('Medios baños', ''),
            'Recamaras': detalles.get('Recamaras', ''),
            'Estacionamientos': detalles.get('Estacionamientos', ''),
            'Edad': detalles.get('Edad', ''),
            'Piso': caracteristicas.get('Piso', ''),
            'Mascotas': caracteristicas.get('Mascotas', ''),
            'Alberca': caracteristicas.get('Alberca', ''),
            'Jacuzzi': caracteristicas.get('Jacuzzi', ''),
            'Cocina integral': caracteristicas.get('Cocina integral', ''),
            'Acceso discapacitados':caracteristicas.get('Acceso discapacitados', ''),
            'Amueblado': caracteristicas.get('Amueblado', ''),
            'Elevador': caracteristicas.get('Elevador', ''),
            'Caseta de guardia': caracteristicas.get('Caseta de guardia', ''),
            'Cuartos de servicio': caracteristicas.get('Cuartos de servicio', ''),
            'Acceso discapacitados': caracteristicas.get('Acceso discapacitados', ''),
            'Frente a Parque': caracteristicas.get('Frente a Parque', ''),
            'Aire acondicionado': caracteristicas.get('Aire acondicionado', ''),
            'Gimnasio': caracteristicas.get('Gimnasio', ''),
            'Terraza': caracteristicas.get('Terraza', ''),
            'Seguridad privada': caracteristicas.get('Seguridad privada', ''),
            'URL': links,
        }

        all_data.append(data)
        # Cerrando el navegador
        #driver.quit()

    # Escribiendo los datos en un archivo CSV
    df = pd.DataFrame(all_data)
    df.to_csv(r'data_parcial_metroscubicos.csv', encoding='utf-8')

    # Cerrando el navegador
    #driver.quit()

    return df

link = ''
results = 100

df = Webscraping_metroscubicos(link, results)
