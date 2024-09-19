import ast

def extract_contect(contenido):
    inicio = contenido.find('{')
    fin = contenido.rfind('}')
    subcadena = ast.literal_eval(f"[{contenido[inicio:fin + 1]}]")
    return subcadena

def total_score(candidatos):
    for candidato in candidatos:
        for _, datos in candidato.items():
            try:
                puntaje_total = sum([valor[0] for valor in datos.values()])
                datos['puntaje_total'] = puntaje_total
            except:
                print(f"Candidato {candidato} no se pudo obtener puntaje total")
    return candidatos

def k_candidates(candidatos, k):
    candidatos_ordenados = sorted(candidatos, key=lambda x: list(x.values())[0]['puntaje_total'], reverse=True)
    mejores_candidatos = candidatos_ordenados[:k]
    return mejores_candidatos

def output_formatted(candidatos):
    resultado = ""
    for candidato in candidatos:
        for nombre, datos in candidato.items():
            resultado += f"\n\n Candidato: {nombre} \n"
            for categoria, valor in datos.items():
                if isinstance(valor, list):
                    resultado += f"\n{categoria.replace('_', ' ').capitalize()}: {valor[1]} (Puntaje: {valor[0]})"
                else:
                    resultado += f"\n{categoria.replace('_', ' ').capitalize()}: {valor}"
    return resultado

