import streamlit as st
import requests
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams
import io
import openai
from dotenv import load_dotenv
import os
import time

from templates import score_cvs, inputs
from processing import extract_contect, total_score, k_candidates, output_formatted


import streamlit as st
import requests
from bs4 import BeautifulSoup
# Reemplazamos pdfminer por PyMuPDF para mayor eficiencia
import fitz  # PyMuPDF
import io
import openai
from dotenv import load_dotenv
import os
import time
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

from templates import score_cvs, inputs
from processing import extract_contect, total_score, k_candidates, output_formatted

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from math import pi
# Cargar variables de entorno
load_dotenv(dotenv_path='variables.env')

# Configurar API de OpenAI
openai.api_key = os.getenv('MODELO_API_KEY')
openai.api_base = os.getenv('MODELO_API_BASE')
openai.api_type = os.getenv('MODELO_API_TIPO')
openai.api_version = os.getenv('MODELO_API_VERSION')

# Configurar API de Teamtailor
API_TOKEN = os.getenv('API_KEY_TEAMTAILOR')
BASE_URL = os.getenv('BASE_URL_TEAMTAILOR')

BATCH_SIZE = int(os.getenv('BATCH_SIZE'))

headers = {
    'Authorization': f'Token token={API_TOKEN}',
    'X-Api-Version': os.getenv('API_VERSION_TEAMTAILOR'),
    'Content-Type': 'application/vnd.api+json'
}

with open('empresas_relevantes.txt', 'r') as file:
    listado_empresas_relevantes = file.read()



seleccionadoss = [
    {
        'name': 'Candidato 1',
        'experiencia_liderando': 80,
        'experiencia_laboral': 70,
        'habilidades': 60,
        'idiomas': 50,
        'empresas_relevantes': 90,
        'estabilidad_laboral': 40,
        'escolaridad': 85
    },
    {
        'name': 'Candidato 2',
        'experiencia_liderando': 60,
        'experiencia_laboral': 80,
        'habilidades': 75,
        'idiomas': 65,
        'empresas_relevantes': 55,
        'estabilidad_laboral': 70,
        'escolaridad': 60
    },
    {
        'name': 'Candidato 3',
        'experiencia_liderando': 50,
        'experiencia_laboral': 40,
        'habilidades': 80,
        'idiomas': 70,
        'empresas_relevantes': 85,
        'estabilidad_laboral': 60,
        'escolaridad': 75
    }
]

# 1. Gráfico de Radar (Spider Chart) - Comparación entre Candidatos
def radar_chart(candidatos):
    # Definir los aspectos evaluados
    aspectos = ['Experiencia Liderando', 'Experiencia Laboral', 'Habilidades', 'Idiomas', 'Empresas Relevantes', 'Estabilidad Laboral', 'Escolaridad']
    num_aspectos = len(aspectos)

    # Crear la figura y los ejes para el gráfico de radar
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))

    # Crear el ángulo para cada aspecto
    angles = [n / float(num_aspectos) * 2 * pi for n in range(num_aspectos)]
    angles += angles[:1]  # Cerrar el gráfico

    # Graficar cada candidato
    for candidato in seleccionadoss:
        puntajes_aspectos = [
            candidato['experiencia_liderando'],
            candidato['experiencia_laboral'],
            candidato['habilidades'],
            candidato['idiomas'],
            candidato['empresas_relevantes'],
            candidato['estabilidad_laboral'],
            candidato['escolaridad']
        ]
        puntajes_aspectos += puntajes_aspectos[:1]  # Cerrar el gráfico

        ax.plot(angles, puntajes_aspectos, linewidth=2, linestyle='solid', label=candidato["name"])
        ax.fill(angles, puntajes_aspectos, alpha=0.25)

    # Añadir las etiquetas de los aspectos
    plt.xticks(angles[:-1], aspectos)

    # Título y leyenda
    ax.set_title("Comparación de Candidatos (Gráfico de Radar)", size=15)
    plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))

    # Mostrar el gráfico en Streamlit
    st.pyplot(fig)
    plt.clf()


def horizontal_bar_chart(candidatos):
    aspectos = ['Experiencia Liderando', 'Experiencia Laboral', 'Habilidades', 'Idiomas', 'Empresas Relevantes', 'Estabilidad Laboral', 'Escolaridad']
    
    for candidato in seleccionadoss:
        puntajes_aspectos = [
            candidato['experiencia_liderando'],
            candidato['experiencia_laboral'],
            candidato['habilidades'],
            candidato['idiomas'],
            candidato['empresas_relevantes'],
            candidato['estabilidad_laboral'],
            candidato['escolaridad']
        ]

        # Crear gráfico de barras horizontales
        fig, ax = plt.subplots(figsize=(8, 5))
        y_pos = np.arange(len(aspectos))
        ax.barh(y_pos, puntajes_aspectos, align='center', color='skyblue')
        ax.set_yticks(y_pos)
        ax.set_yticklabels(aspectos)
        ax.invert_yaxis()  # Invertir el eje y para que el primer aspecto esté arriba
        ax.set_xlabel('Puntaje')
        ax.set_title(f'Adecuación de {candidato["name"]} a la Job Description')

        # Mostrar el gráfico en Streamlit
        st.pyplot(fig)
        plt.clf()

# Definir la función principal
def main():
    st.title("Pre-screening candidatos")
    
    # Crear cuadros de texto en la interfaz de usuario
    job_id = st.text_input("Ingresa el identificador del trabajo (el número que está en la URL):")
    k = st.number_input("Número de CVs a seleccionar (k):", min_value=1, value=5, step=1)

    años_experiencia_liderando = st.number_input("Puntaje para años de experiencia liderando:", min_value=0, max_value=100, value=0, step=1)
    años_experiencia_laboral = st.number_input("Puntaje para años de experiencia laboral:", min_value=0, max_value=100, value=35, step=1)
    habilidades = st.number_input("Puntaje para habilidades:", min_value=0, max_value=100, value=35, step=1)
    idiomas = st.number_input("Puntaje para idiomas:", min_value=0, max_value=100, value=0, step=1)
    empresas_relevantes = st.number_input("Puntaje para empresas relevantes:", min_value=0, max_value=100, value=20, step=1)
    estabilidad_laboral = st.number_input("Puntaje para estabilidad laboral:", min_value=0, max_value=100, value=5, step=1)
    escolaridad = st.number_input("Puntaje para escolaridad:", min_value=0, max_value=100, value=5, step=1)

    total_puntaje = (
        años_experiencia_liderando +
        años_experiencia_laboral +
        habilidades +
        idiomas +
        empresas_relevantes +
        estabilidad_laboral +
        escolaridad
    )
    
    # Botón para ejecutar el análisis
    page_number = 1
    page_size = 30 
    has_more = True
    if st.button("Ejecutar"):
        if total_puntaje != 100:
            st.error(f"La suma de los puntajes debe ser exactamente 100. Actualmente es {total_puntaje}.")
        else:
            start_time = time.time()
            with st.spinner('Procesando...'):
                response = requests.get(f'{BASE_URL}/jobs/{job_id}', headers=headers)
                
                if response.status_code == 200:
                    try:
                        job = response.json()['data']
                        job_description_html = job['attributes']['body']
                    except:
                        st.error(f"La requisición {job_id} no tiene jobs creados")

                    # Parsear la descripción del trabajo
                    soup = BeautifulSoup(job_description_html, 'html.parser')
                    job_description_text = soup.get_text(separator="\n", strip=True)

                    # Obtener candidatos vinculados al job
                    cvs = []
                    while has_more:
                        response_candidates = requests.get(f'{BASE_URL}/jobs/{job_id}/candidates?page[size]={page_size}&page[number]={page_number}', headers=headers)
                        data = response_candidates.json()['data']
                    
                        for candidate in data:
                            resume_url = candidate['attributes']['resume']
                            candidate_id = candidate['id']
                            candidate_name = candidate['attributes']['first-name'] + ' ' + candidate['attributes']['last-name']
                            try:
                                resume_response = requests.get(resume_url)
                                pdf_file = io.BytesIO(resume_response.content)
                                laparams = LAParams()  
                                resume_text = extract_text(pdf_file, laparams=laparams).strip()
                                cvs.append(resume_text)
                            except:
                                print(f"ID: {candidate_id}, Nombre: {candidate_name} no se pudo extraer la hoja de vida")

                        if len(data) < page_size:
                            has_more = False
                        else:
                            page_number += 1
                    
                    hojas_de_vida = len(cvs)
                    # Enviar la solicitud a OpenAI
                    all_responses = []
                    while len(cvs) > 0:
                        response = openai.ChatCompletion.create(
                            engine=os.getenv('DEPLOYMENT_NAME'),
                            messages=[
                                {"role": "system", "content": score_cvs(años_experiencia_liderando,
                                                                        años_experiencia_laboral, 
                                                                        habilidades, idiomas, 
                                                                        empresas_relevantes, 
                                                                        estabilidad_laboral, 
                                                                        escolaridad,
                                                                        listado_empresas_relevantes)},
                                {"role": "user", "content": inputs(job_description_text, cvs[:BATCH_SIZE])}
                            ],
                            temperature=0.0
                        )
                        modelo_respuesta = response["choices"][0]["message"]["content"]
                        respuesta_formateada = extract_contect(modelo_respuesta)
                        puntaje_total = total_score(respuesta_formateada)
                        all_responses.extend(puntaje_total)
                        cvs = cvs[BATCH_SIZE:] 

                    seleccionados = k_candidates(all_responses, k)
                    output_final = output_formatted(seleccionados)
                    st.success("Respuesta del modelo:")
                    end_time = time.time() 
                    execution_time = int(end_time - start_time)
                    st.write(f"Tiempo de ejeución: {execution_time} segundos \n\n Total candidatos revisados: {hojas_de_vida}\n\n {output_final}")
                    radar_chart(seleccionados)
                    horizontal_bar_chart(seleccionados)
                else:
                    st.error("Error al obtener la información del trabajo.")

if __name__ == "__main__":
    main()