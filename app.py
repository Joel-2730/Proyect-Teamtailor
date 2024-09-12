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

# Cargar variables de entorno
load_dotenv()

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
                else:
                    st.error("Error al obtener la información del trabajo.")

if __name__ == "__main__":
    main()
