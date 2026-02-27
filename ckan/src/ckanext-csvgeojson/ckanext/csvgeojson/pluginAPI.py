from ckan.plugins import SingletonPlugin, implements
from ckan.plugins.interfaces import IConfigurer, IBlueprint
from ckan.plugins import toolkit
from ckan.common import config
import ckan.model as model
from ckan.model.resource import Resource  # ✅ Correcto import

from flask import Blueprint, jsonify, redirect, request, Response

import logging, json, subprocess, os


log = logging.getLogger(__name__)


class DataJson(SingletonPlugin):
    implements(IBlueprint)
    log.info("[DataJson] DataJson Cargado con Exito")

    def update_config(self, config):
        log.info("[DataJson] update_config ejecutado")

    
    def get_blueprint(self):

        bp = Blueprint('data_json', __name__)

        log.info("[DataJson] get_blueprint_geojson ejecutado")

        @bp.route('/api/3/action/data.json', methods=['GET'])
        def dataJson():

            #log.info("[DataJson] get_blueprint powerBI ejecutado")
            context = {
                'model': model,
                'session': model.Session,
                'ignore_auth': True,
                'user': None
            }

            data={}
            try:

                # 1️⃣ Primero obtengo la cantidad total
                count_result = toolkit.get_action('package_search')(context, {
                    'rows': 0
                })
                registros = count_result['count']

                # 2️⃣ Ahora hago otra llamada trayendo exactamente esa cantidad
                responses = toolkit.get_action('package_search')(context, {
                    'rows': registros
                })



                package_responses=responses['results']

                log.warning(f"[DataJson] get_blueprint dataJson responses: {package_responses}")


                data={
                        "@context": "https://project-open-data.cio.gov/v1.1/schema/catalog.jsonld",
                        "@type": "dcat:Catalog", 
                        "conformsTo": "https://project-open-data.cio.gov/v1.1/schema", 
                        "describedBy": "https://project-open-data.cio.gov/v1.1/schema/catalog.json",
                    }

                data['dataset']=[]

                url_site=config.get('ckan.site_url')


                count=0

                for package_response in package_responses:
                        

                    #log.warning(f"[DataJson] get_blueprint powerBI  {package_response['id']} posicion {count}') : {registros}")

                    if package_response.get('type', '').lower() != 'harvest':

                        grupos= package_response.get('groups')
                        organization=package_response.get('organization') 
                        tags=package_response.get('tags') 
                        resources=package_response.get('resources') 

                        if package_response.get('private')==True:
                            estado="Privado"
                        else:
                            estado="Público"

                        data_dataset={
                            "@type":"Dataset",
                            "identifier":package_response['id'], 
                            "landingPage":"{}".format(url_site+'/'+package_response.get('type')+'/'+package_response['id']),  
                            "title": package_response.get('title'),
                            "description": package_response.get('notes'),
                            "dependencia":organization.get('title') if organization else '',
                            "issued": package_response.get('metadata_created') or '',
                            "modified": package_response.get('metadata_modified') or '',
                            "ciudad": package_response.get('ciudad') or '' ,
                            "departamento":package_response.get('departamento') or '',
                            "accrualPeriodicity":package_response.get('frecuencia_actualizacion') or '',
                            "keywords":[tag["display_name"] for tag in tags],
                            "publisher":{
                                "@type": "org:Organization",
                                "name": "{}".format("org:"+ organization.get('title') if organization else ''),
                            },
                            "contactPoint":{
                                "@type": "vcard:Contact", 
                                "hasEmail": "mailto:datosabiertos@valledelcauca.gov.co", 
                                "fn":  "Valle Data"
                            },
                            "accessLevel":estado,
                            'license':{}                   
                        }


                        data_dataset['distribution']=[]
                        data_dataset['theme']=[]

                        if grupos:
                            data_dataset['theme'].append(grupos)

                        for resource in resources:
                            data_resource= {
                                "@type": "dcat:Distribution",
                                "description":resource.get('description') or '',
                                "downloadURL":resource.get('url') or '',  
                                "format":resource.get('format') or '',
                                "mediaType":resource.get('mediaType') or '',
                                "title":resource.get('title') or '',
                                "issued": resource.get('created') or '',
                                "modified": resource.get('last_modified') or ''
                            }

                            data_dataset['distribution'].append(data_resource)
                    data['dataset'].append(data_dataset)
                return  jsonify(data) 
                #return Response(json.dumps(data), mimetype="application/json")

            except Exception as e:
                log.error(f"[DataJson] Error procesando get_blueprint powerBI: {e}")    



        

        @bp.route('/api/3/action/powerBI.json', methods=['GET'])
        def powerBI():

            """
            EndPoint para Tableros
            """

            #log.info("[DataJson] get_blueprint powerBI ejecutado")
            context = {
                'model': model,
                'session': model.Session,
                'ignore_auth': True,
                'user': None
            }

            

            data={}
            try:

                # 1️⃣ Primero obtengo la cantidad total
                count_result = toolkit.get_action('package_search')(context, {
                    'rows': 0,
                    'include_private': True,
                    'fq': '+state:active'
                })
                registros = count_result['count']

                # 2️⃣ Ahora hago otra llamada trayendo exactamente esa cantidad
                responses = toolkit.get_action('package_search')(context, {
                    'rows': registros,
                    'include_private': True,
                    'fq': '+state:active'
                })
                

                package_responses=responses['results']

                #log.warning(f"[DataJson] get_blueprint powerBI context: {context}")

                log.warning(f"[DataJson] get_blueprint powerBI responses: {package_responses}")

                #
                # log.warning(f"[DataJson] get_blueprint powerBI registros: {registros}")

                if package_responses:
                    
                    data={
                        "@context": "https://project-open-data.cio.gov/v1.1/schema/catalog.jsonld",
                        "@type": "dcat:Catalog", 
                        "conformsTo": "https://project-open-data.cio.gov/v1.1/schema", 
                        "describedBy": "https://project-open-data.cio.gov/v1.1/schema/catalog.json",
                    }

                    data['conjuntoDatos']=[]
                    data['sellos']=[]

                    url_site=config.get('ckan.site_url')


                    count=0

                    
                    for package_response in package_responses:

                        #log.warning(f"[DataJson] get_blueprint powerBI  {package_response['id']} posicion {count}') : {registros}")

                        if package_response.get('type', '').lower() != 'harvest':

                            grupos= package_response.get('groups')
                            organization=package_response.get('organization') 
                            tags=package_response.get('tags') 
                            resources=package_response.get('resources') 

                            estado=None    
                            if package_response.get('private')==True:
                                estado="Privado"
                            else:
                                estado="Público"

                            consolidado=package_response.get('consolidado')

                            #log.warning(f"[DataJson] get_blueprint powerBI organization: {organization}")

                            data_dataset={
                                "@type":"Dataset",
                                "identifier":package_response['id'], 
                                "landingPage":"{}".format(url_site+'/'+package_response.get('type')+'/'+package_response['id']),  
                                 "title": package_response.get('title'),
                                "description": package_response.get('notes'),
                                "dependencia":organization.get('title') if organization else '',
                                "issued": package_response.get('metadata_created') or '',
                                "modified": package_response.get('metadata_modified') or '',
                                "ciudad": package_response.get('ciudad') or '' ,
                                "departamento":package_response.get('departamento') or '',
                                "frecuencia_actualizacion":package_response.get('frecuencia_actualizacion') or '',
                                "keywords":[tag["display_name"] for tag in tags],
                                "publisher":{
                                    "@type": "org:Organization",
                                    "name": "{}".format("org:"+ organization.get('title') if organization else ''),
                                },
                                "contactPoint":{
                                    "@type": "vcard:Contact", 
                                    "hasEmail": "mailto:datosabiertos@valledelcauca.gov.co", 
                                    "fn":  "Valle Data"
                                },
                                "accessLevel":estado,
                                'licencia':{},
                                "Visualizaciones":consolidado.get('visualizaciones') if consolidado else 0,
                                "descargar":consolidado.get('descargas') if consolidado else 0,                                   
                            }

                            data_dataset['distribucion']=[]
                            data_dataset['tema']=[]

                            if grupos:
                                data_dataset['tema'].append(grupos)
                           
                           
                            for resource in resources:

                               
                                contador=resource.get('contador')
                                estructura=resource.get('estructura')
                                data_extras=resource.get('data_extra')
                                #log.warning(f"[DataJson] get_blueprint powerBI contador: {contador}")
                                #log.warning(f"[DataJson] get_blueprint powerBI estructura: {estructura}")
                                #log.warning(f"[DataJson] get_blueprint powerBI data_extras: {data_extras}")

                                

                                categoria=data_extras.get('categoria') if data_extras else ''    
                                #log.warning(f"[DataJson] resource {resource['id']} categoria: {categoria}")


                                if categoria:

                                    
                                    data_sello={
                                    "@type": "dcat:Sello", 
                                    "description":resource.get('description') or '',
                                    "downloadURL":resource.get('url') or '',
                                    "format":resource.get('format') or '',
                                    "mediaType":resource.get('mediaType') or '',
                                    "title":resource.get('title') or '',
                                    'filas':estructura.get('filas') if estructura else 0,
                                    'columnas':estructura.get('columnas') if estructura else 0,
                                    "vistas":contador.get('visualizaciones') if contador else 0,
                                    'descargas':contador.get('descargas') if contador else 0,
                                    'categoria':data_extras.get('categoria') if data_extras else '',
                                    'fecha_obtencion':data_extras.get('fecha_obtencion') if data_extras else '',
                                    'fecha_vencimiento':data_extras.get('fecha_vencimiento') if data_extras else '',
                                    'dependiencia':data_extras.get('dependiencia') if data_extras else '',
                                    'nivel':data_extras.get('nivel') if data_extras else '',
                                    
                                    }

                                    #log.warning(f"[DataJson] resource {resource['id']} categoria: {categoria} data_sello {data_sello}")

                                    #name_sello=resource.get('name')
                                    data['sellos'].append(data_sello)

                                else: 

                                    if resource.get('format')=='CSV' and str(resource.get("datastore_active", "")).lower() == "true" and str(resource.get("type", "")).lower() != "sello_excelencia":

                                        data_resource= {
                                            "@type": "dcat:Distribution",
                                            "description":resource.get('description') or '',
                                            "downloadURL":resource.get('url') or '',  
                                            "format":resource.get('format') or '',
                                            "mediaType":resource.get('mediaType') or '',
                                            "title":resource.get('title') or '',
                                            "issued": resource.get('created') or '',
                                            "modified": resource.get('last_modified') or '',                              
                                            "filas":estructura.get('filas') if estructura else 0 ,
                                            "columnas":estructura.get('columnas') if estructura else 0 ,
                                            "vistas":contador.get('visualizaciones') if contador else 0,
                                            'descargas':contador.get('descargas') if contador else 0,
                                        }

                                        #log.warning(f"[DataJson] resource {resource['id']} categoria: {categoria} data_resource {data_resource}")
                                        #nombre_resource=resource.get('name')
                                        data_dataset['distribucion'].append(data_resource)

                               

                                #log.warning(f"[DataJson] get_blueprint powerBI resources_response: {resource}")

                        #log.warning(f"[DataJson] get_blueprint powerBI data_dataset: {data_dataset}")
                        data['conjuntoDatos'].append(data_dataset)

                        #log.warning(f"[DataJson] get_blueprint powerBI data_dataset: {data_dataset}")

                        count+=1
                            
                return  jsonify(data) 
                #return Response(json.dumps(data), mimetype="application/json")

            except Exception as e:
                log.error(f"[DataJson] Error procesando get_blueprint dataset: {e}")

            # Siempre devolver success para no interrumpir CKAN

            #return jsonify({"success": True})
            
        return bp 
    
    