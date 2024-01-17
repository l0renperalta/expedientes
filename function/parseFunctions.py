from lxml import html
from Class.ClasesExpediente import (
    ReporteDeExpediente,
    ParteProceso,
    Seguimiento,
    Notificacion,
)
import json
import os
import boto3
from botocore.exceptions import NoCredentialsError
from selenium.webdriver.common.by import By
import time
import PyPDF2
from bs4 import BeautifulSoup as bs
import subprocess

bucket_name = "expedientespjvf"
s3_file_name = "nombre-en-s3/archivo.json"
download_path = os.path.join(os.getcwd(), "exp", "files")

def extract_expediente_info(html_content, nombre, driver):
    try:
        expediente = ReporteDeExpediente()
        doc = html.fromstring(html_content[0])
        # Extraer valores y llenar el objeto reporte_de_expediente
        expediente.NumeroExpediente = get_value_by_label(doc, "Expediente N°:")
        expediente.OrganoJurisdiccional = get_value_by_label(
            doc, "Órgano Jurisdiccional:"
        )
        expediente.DistritoJudicial = get_value_by_label(doc, "Distrito Judicial:")
        expediente.Juez = get_value_by_label(doc, "Juez:")
        expediente.EspecialistaLegal = get_value_by_label(doc, "Especialista Legal:")
        expediente.FechaInicio = get_value_by_label(doc, "Fecha de Inicio:")
        expediente.Proceso = get_value_by_label(doc, "Proceso:")
        expediente.Observacion = get_value_by_label(doc, "Observación:")
        expediente.Especialidad = get_value_by_label(doc, "Especialidad:")
        expediente.Materias = get_value_by_label(doc, "Materia(s):")
        expediente.Estado = get_value_by_label(doc, "Estado:")
        expediente.EtapaProcesal = get_value_by_label(doc, "Etapa Procesal:")
        expediente.FechaConclucion = get_value_by_label(doc, "Fecha Conclusión:")
        expediente.Ubicacion = get_value_by_label(doc, "Ubicación:")
        expediente.MotivoConclucion = get_value_by_label(doc, "Motivo Conclusión:")
        expediente.Sumilla = get_value_by_label(doc, "Sumilla:")

        data = get_values_partes_procesales(html.fromstring(html_content[1]))
        partes_procesales = []
        # Extraer valores y llenar el objeto parte_proceso
        for elemento in data:
            proceso = ParteProceso()
            proceso.Rol = elemento[0] if len(elemento) > 0 else ""
            proceso.TipoPersona = elemento[1] if len(elemento) > 1 else ""
            proceso.ApellidoPaterno = elemento[2] if len(elemento) > 2 else ""
            proceso.ApellidoMaterno = elemento[3] if len(elemento) > 3 else "" # verifica si existe la posicion 4
            proceso.NombresORazonSocial = elemento[4] if len(elemento) > 4 else "" # verifica si existe la posicion 5

            partes_procesales.append(proceso.__dict__)


        seguimiento_data = get_values_seguimiento_expediente(html.fromstring(html_content[2]), driver)
        expedientes_seguimiento = []
        # Extraer valores y llenar el objeto seguimiento_expediente
        for element in seguimiento_data:
            seguimiento = Seguimiento()
            seguimiento.NumeroEsquina = element[0]
            seguimiento.FechaResolucion = element[1]
            seguimiento.Resolucion = element[2]
            seguimiento.TipoNotificacion = element[3]
            seguimiento.Acto = element[4]
            seguimiento.Fojas = element[5]
            seguimiento.FechaProveido = element[6]
            seguimiento.Sumilla = element[7]
            seguimiento.DescripcionUsuario = element[8]
            seguimiento.EnlaceDescarga = element[9]

            notificacion = Notificacion()
            notificaciones = []  

            for n in element[10]:
                notificacion = Notificacion()  

                notificacion.Destinatario = n[0]
                notificacion.Anexos = n[1]
                notificacion.FechaResolucion = n[2]
                notificacion.FechaNotificacionImpresa = n[3]
                notificacion.FechaEnviadaCentralNotificacion = n[4]
                notificacion.FechaRecepcionadaCentralNotificacion = n[5]
                notificacion.FechaNotificacionDestinatario = n[6]
                notificacion.FechaCargoDevueltoJuzgado = n[7]
                notificacion.FormaEntrega = n[8]

                notificaciones.append(notificacion.__dict__)  

            seguimiento.Notificaciones = notificaciones
            expedientes_seguimiento.append(seguimiento.__dict__)

        data_combinada = { **expediente.__dict__, "partes_procesales": partes_procesales, "expedientes_seguimiento": expedientes_seguimiento }
        
        json_data = json.dumps(data_combinada, indent=4)
        json_file_path = os.path.join("./exp", f"{nombre}.json")
        with open(json_file_path, "w") as file:
            file.write(json_data)

        # s3 = boto3.client('s3',aws_access_key_id='AKIAVNIGRL6VQALTCM77', aws_secret_access_key='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')
        # s3.upload_file(json_file_path, bucket_name, f'expedientes/{nombre}.json', ExtraArgs={'ContentType': 'application/json'})
        # os.remove(json_file_path)
    except Exception as e:
        print("Error: " + str(e))


def get_value_by_label(doc, label):
    # La expresión XPath busca el div que contiene el texto de la etiqueta y luego selecciona el div hermano
    xpath_expression = f"//div[contains(@class, 'celdaGridN') and contains(text(), '{label}')]/following-sibling::div[contains(@class, 'celdaGrid')]"
    nodes = doc.xpath(xpath_expression)

    if nodes:
        # Obtener el primer nodo y buscar texto en él o en sus elementos hijos
        node = nodes[0]
        if node.text:
            return node.text.strip()
        elif node.find(".//") is not None and node.find(".//").text:
            return node.find(".//*").text.strip()
    return ""


def get_values_partes_procesales(doc):
    # Obtener todos los div con clase partes dentro del div panelGrupo
    partes_divs = doc.xpath("//div[contains(@class, 'panelGrupo')]//div[contains(@class, 'partes')]")
    results = []

    for div in partes_divs:
        children = div.xpath("./*")  # Obtener todos los hijos del div actual
        div_texts = []

        for element in children:
            node_text = (element.text.strip() if element.text else element.find(".//*").text.strip())
            div_texts.append(node_text)

        results.append(div_texts)

    return results[1:]


def get_values_seguimiento_expediente(doc, driver):
    # elements = doc.xpath("//div[contains(@id, 'collapseThree')]/*")
    # driver.execute_script("arguments[0].style.display = 'block';", element) for element in elements       change display: to none to block

    result = []
    count = 1
    seguimiento_count = doc.xpath('//*[@id="collapseThree"]/*')
    firstDownloaded = False
    setLastFileId = 0
    
    for i in range(2, len(seguimiento_count) + 1):
        expediente = []
        expediente.append(count)
        
        exp_data = doc.xpath(f"//div[contains(@id, 'collapseThree')]/div[{i}]//div[contains(@class, 'row')]//div[contains(@class, 'borderinf')]")
        for element in exp_data:
            expediente.append(element[1].text.strip()) if element[1].text else expediente.append("")
        
        download = doc.xpath(f"//div[contains(@id, 'collapseThree')]/div[{i}]//div[contains(@class, 'row')]//div[@class='dBotonDesc']/a")
        if len(download) != 0 and not firstDownloaded:
            setLastFileId = i
            firstDownloaded = True
        else:
            expediente.append("")

        notificaciones = []
        notifications_count = doc.xpath(f"//*[@id='pnlSeguimiento{count}']//*[@id='divResol']/div[1]/div[2]/*")
        
        if len(notifications_count) != 0:        
            for i in range(1, len(notifications_count) + 1):
                notificacion = []
                noti_data = doc.xpath(f"//*[@id='modal-dialog-{count}-{i}']/div/div[2]/div/div//div[contains(@class, 'rowNotif')]")
                
                for element in noti_data[:-1]: # for para agregar los datos a la lista notificacion
                    notificacion.append(element[1].text.strip()) if element[1].text else notificacion.append('') # se agrega a la lista notificacion los datos del modal

                notificaciones.append(notificacion)
        
        expediente.append(notificaciones)
        
        result.append(expediente)
        count = count + 1
    
    # añadir el ultimo archivo al json
    texto = downloadLastExp(setLastFileId, driver)
    indice_ultimo = len(result[setLastFileId-2]) - 1
    result[setLastFileId-2].insert(indice_ultimo, texto)

    return result # [..., [[...],[...]]]
    
def downloadLastExp(setLastFileId, driver):
    driver.find_element(By.XPATH, f"//div[contains(@id, 'collapseThree')]/div[{setLastFileId}]//div[contains(@class, 'row')]//div[@class='dBotonDesc']/a").click()
    time.sleep(1)

    archivo = os.listdir(download_path)[0]
    if archivo.endswith(".pdf"):
        reader = PyPDF2.PdfReader(f"{download_path}\\{archivo}")
        texto = reader.pages[0].extract_text()
        return texto
    
    if archivo.endswith(".doc"):
        try:
            result = subprocess.run(['antiword', os.path.join(download_path, archivo)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0:
                return result.stdout
            else:
                print(f"Error: {result.stderr}")
                return None

        except Exception as e:
            print(f"An error occurred: {e}")
            return None
        
        # texto = subprocess.check_output(['antiword', os.path.join(download_path, file_name)], text=True)
        # print(type(texto))
        # print(texto)
        # return texto

    
    # if archivo.endswith(".doc"):
        # text = get_doc_text(download_path, archivo)
        # print(text)

        # with open(f"{download_path}\\{archivo}", 'r', encoding='utf-8', errors='ignore') as file:
        #     soup = bs(file.read())
        #     [s.extract() for s in soup(['style', 'script'])]
        #     tmpText = soup.get_text()
        #     texto = "".join("".join(tmpText.split('\t')).split('\n')).encode('utf-8').strip()
        #     # texto = docx2txt.process(texto)
        #     # print(texto)
        #     extraer_texto_desde_bytes(texto)
        #     return texto
        
# def get_doc_text(filepath, file):
#     if file.endswith('.docx'):
#        text = docx2txt.process(file)
#        return text
#     elif file.endswith('.doc'):
#        # converting .doc to .docx
#        doc_file = filepath + file
#        docx_file = filepath + file + 'x'
#        if not os.path.exists(docx_file):
#           os.system('antiword ' + doc_file + ' > ' + docx_file)
#           with open(docx_file) as f:
#              text = f.read()
#           os.remove(docx_file) #docx_file was just to read, so deleting
#        else:
#           # already a file with same name as doc exists having docx extension, 
#           # which means it is a different file, so we cant read it
#           print('Info : file with same name of doc exists having docx extension, so we cant read it')
#           text = ''
#        return text
       

# def extraer_texto_desde_bytes(doc_bytes):
#     try:
#         temp_file_path = f"{download_path}\\pr1.docx"
#         with open(temp_file_path, 'wb') as temp_file:
#             temp_file.write(doc_bytes)

#         # Extraer texto del archivo temporal
#         texto = docx2txt.process(temp_file_path)

#         # Imprimir el texto o devolverlo según tus necesidades
#         print(texto)

#     except Exception as e:
#         print(f"Error al extraer texto: {e}")

#     finally:
#         # Eliminar el archivo temporal
#         if os.path.exists(temp_file_path):
#             os.remove(temp_file_path)

