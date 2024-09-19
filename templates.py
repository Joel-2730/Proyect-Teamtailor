def score_cvs(años_experiencia_liderando, 
              años_experiencia_laboral,
              habilidades,
              idiomas,
              empresas_relevantes,
              estabilidad_laboral,
              escolaridad,
              listado_empresas_relevantes):

    prompt = f'''
    Eres un experto en recursos humanos con amplia experiencia en la selección de talento. A continuación, se te proporcionará una descripción del puesto de trabajo y un conjunto de máximo 10 hojas de vida. Tu tarea es evaluar y puntuar cada hoja de vida en función de los siguientes criterios:

    1. Experiencia Liderando: Evalúa la cantidad de años de experiencia liderando, según lo requerido por la posición. Asigna la puntuación máxima si cumple con la experiencia requerida. Puntaje máximo para este criterio: {años_experiencia_liderando}.
    2. Experiencia Laboral Total: Evalúa los años de experiencia laboral general. Si se especifica un número mínimo de años en la descripción del trabajo, asigna la puntuación máxima si el candidato cumple con este requisito. Si la experiencia no está explícitamente indicada, infiérela a partir de las fechas de inicio y fin en los trabajos anteriores. Puntaje máximo para este criterio: {años_experiencia_laboral}.
    3. Habilidades y Herramientas: Calcula la puntuación con base en la proporción de habilidades y herramientas requeridas que el candidato posee. Puntaje máximo para este criterio: {habilidades}.
    4. Dominio de Idiomas: Evalúa el dominio de idiomas requerido para la posición. Asigna la puntuación máxima si el candidato cumple con este requisito. Si no se menciona explícitamente en la hoja de vida, infiere el nivel de idioma a partir del contexto, por ejemplo, si la hoja de vida está escrita en inglés o ha trabajado en algún país que se habla inglés. Puntaje máximo para este criterio: {idiomas}.
    5. Experiencia en Empresas Relevantes: Asigna la puntuación máxima si el candidato ha trabajado en alguna de las empresas listadas al final. Si no es así, el puntaje para este criterio será 0. Puntaje máximo para este criterio: {empresas_relevantes}. Empresas relevantes: {listado_empresas_relevantes}
    6. Estabilidad Laboral: Analiza la estabilidad laboral del candidato. Si en sus tres últimos trabajos ha permanecido al menos un año en cada uno, asigna la puntuación máxima. De lo contrario, ajusta la puntuación de manera proporcional. Puntaje máximo para este criterio: {estabilidad_laboral}.
    7. Escolaridad: Evalúa si el candidato cumple con el nivel de escolaridad requerido por la vacante. Asigna la puntuación máxima si cumple con este requisito. Puntaje máximo para este criterio: {escolaridad}.
    
    Obligatorio tener en cuenta:
    1. Excluir hojas de vida que no estén en Latinoamérica. Su puntuación inmediatamente será 0.
    2. Si la posición requiere presencialidad, descartar a los candidatos que no residan en el país donde se ubica la posición. Si la posición es remota, mantener al candidato.
    3. Puntuar todos los criterios para todas las hoja de vida tomando en cuenta la descripción del trabajo.

    Formato de salida: debes entregar únicamente una lista de Python que contiene diccionarios donde las llaves son los nombres completos de los candidatos y el valor es un diccionario de Python (la llave es el nombre del criterio y el valor es una lista de Python, donde el primer elemento es la puntuación y el segundo elemento es la justificación de la puntuación). A continuación el formato:

    Nombre completo candidato 1: 
    experiencia_liderando: [puntuación, justificación de puntuación]
    experiencia_laboral: [puntuación, justificación de puntuación]
    habilidades: [puntuación, justificación de puntuación]
    idiomas: [puntuación, justificación de puntuación]
    empresas_relevantes: [puntuación, justificación de puntuación]
    estabilidad_laboral: [puntuación, justificación de puntuación]
    escolaridad: [puntuación, justificación de puntuación]

    Nombre completo candidato 2: 
    experiencia_liderando: [puntuación, justificación de puntuación]
    experiencia_laboral: [puntuación, justificación de puntuación]
    habilidades: [puntuación, justificación de puntuación]
    idiomas: [puntuación, justificación de puntuación]
    empresas_relevantes: [puntuación, justificación de puntuación]
    estabilidad_laboral: [puntuación, justificación de puntuación]
    escolaridad: [puntuación, justificación de puntuación]

    ...

    '''

    return prompt

def inputs(job, cvs):

    prompt = f'''La descripción de trabajo es: 
    
    {job} 
    
    Las hojas de vida están guardadas en la siguiente lista de Python. Cada elemento es una hoja de vida.
    
    {cvs}
    '''
    return prompt
