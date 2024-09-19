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

# Cargar variables de entorno
dotenv_path = os.path.join(os.path.dirname(__file__), 'variables.env')
load_dotenv(dotenv_path=dotenv_path)

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
                        return  # Salir de la función si hay un error

                    # Parsear la descripción del trabajo
                    soup = BeautifulSoup(job_description_html, 'html.parser')
                    job_description_text = soup.get_text(separator="\n", strip=True)

                    # Obtener candidatos vinculados al job
                    candidate_info = []
                    while has_more:
                        response_candidates = requests.get(f'{BASE_URL}/jobs/{job_id}/candidates?page[size]={page_size}&page[number]={page_number}', headers=headers)
                        data = response_candidates.json()['data']

                        for candidate in data:
                            resume_url = candidate['attributes']['resume']
                            candidate_id = candidate['id']
                            candidate_name = candidate['attributes']['first-name'] + ' ' + candidate['attributes']['last-name']
                            candidate_info.append({
                                'id': candidate_id,
                                'name': candidate_name,
                                'resume_url': resume_url
                            })

                        if len(data) < page_size:
                            has_more = False
                        else:
                            page_number += 1

                    hojas_de_vida = len(candidate_info)

                    # Descargar hojas de vida asíncronamente
                    async def fetch_resume(session, candidate):
                        resume_url = candidate['resume_url']
                        try:
                            async with session.get(resume_url) as response:
                                if response.status == 200:
                                    content = await response.read()
                                    return candidate, content
                                else:
                                    print(f"ID: {candidate['id']}, Nombre: {candidate['name']} no se pudo descargar la hoja de vida")
                                    return candidate, None
                        except Exception as e:
                            print(f"ID: {candidate['id']}, Nombre: {candidate['name']} error al descargar: {e}")
                            return candidate, None

                    async def download_resumes(candidates):
                        async with aiohttp.ClientSession() as session:
                            tasks = [fetch_resume(session, candidate) for candidate in candidates]
                            return await asyncio.gather(*tasks)

                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    resumes = loop.run_until_complete(download_resumes(candidate_info))
                    loop.close()

                    # Filtrar los resumes descargados exitosamente
                    valid_resumes = [(candidate, content) for candidate, content in resumes if content is not None]

                    # Extraer texto de los PDFs en paralelo
                    def extract_resume_text(args):
                        candidate, pdf_bytes = args
                        try:
                            pdf_file = io.BytesIO(pdf_bytes)
                            with fitz.open(stream=pdf_file, filetype='pdf') as doc:
                                text = ""
                                for page in doc:
                                    text += page.get_text()
                            return text.strip()
                        except Exception as e:
                            print(f"ID: {candidate['id']}, Nombre: {candidate['name']} no se pudo extraer la hoja de vida: {e}")
                            return None

                    with ThreadPoolExecutor() as executor:
                        cvs = list(executor.map(extract_resume_text, valid_resumes))

                    # Filtrar los textos extraídos exitosamente
                    cvs = [cv for cv in cvs if cv is not None]

                    # Enviar la solicitud a OpenAI
                    all_responses = []
                    cvs_copy = cvs.copy()  # Hacemos una copia para no modificar la lista original
                    while len(cvs_copy) > 0:
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
                                {"role": "user", "content": inputs(job_description_text, cvs_copy[:BATCH_SIZE])}
                            ],
                            temperature=0.0
                        )
                        modelo_respuesta = response["choices"][0]["message"]["content"]
                        respuesta_formateada = extract_contect(modelo_respuesta)
                        puntaje_total = total_score(respuesta_formateada)
                        all_responses.extend(puntaje_total)
                        cvs_copy = cvs_copy[BATCH_SIZE:] 

                    seleccionados = k_candidates(all_responses, k)
                    output_final = output_formatted(seleccionados)
                    st.success("Respuesta del modelo:")
                    end_time = time.time() 
                    execution_time = int(end_time - start_time)
                    st.write(f"Tiempo de ejecución: {execution_time} segundos \n\n Total candidatos revisados: {hojas_de_vida}\n\n {output_final}")
                else:
                    st.error("Error al obtener la información del trabajo.")

if __name__ == "__main__":
    main()
