
from ckan.plugins import SingletonPlugin, IDatasetForm, implements, IPackageController, IResourceController
from ckan.plugins import toolkit
from ckan.plugins.interfaces import IResourceView, IConfigurer, IBlueprint
from flask import Blueprint,request
import json, logging,os,  mimetypes
from datetime import datetime, date
import ckan.logic as logic
import ckan.model as model
from model import Session, Resource,Package,PackageExtra,Contador
import fitz  
from ckan.types import Context 
from ckan.common import config
from typing import Any
import pprint, re                    
from ckanext.csvgeojson.services.geojson_converter import GeoJSONConverter
import ckan.lib.helpers as h
from ckan.common import request
from ckan.lib.helpers import flash_error, redirect_to
from sqlalchemy.orm import joinedload
from dateutil.relativedelta import relativedelta
from configparser import ConfigParser


logging.basicConfig(
    filename="/var/log/ckan/power_BI_json.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

log = logging.getLogger(__name__)

def get_ckan_config():

    log.info("[convert_job] get_ckan_config ejecutado")
    
    
    # Ruta a tu production.ini
    ini_path = "/etc/ckan/default/produccion.ini"  # cámbiala según tu instalación
    storage_path = '/var/lib/ckan/default/'

    config_ckan = ConfigParser()
    config_ckan.read(ini_path)

    # CKAN guarda las variables en la sección [app:main]
    site_url = config_ckan.get("app:main", "ckan.site_url", fallback=None)
    api_key = config_ckan.get("app:main", "ckan.datapusher.api_token", fallback=None)
    ssl_cert = config_ckan.get("app:main", "ckan.devserver.ssl_cert", fallback=None)
   
    
    #api_key = os.environ.get("CKAN_API_KEY")  # mejor manejarlo como variable de entorno

    log.info("[powerBI.py][get_ckan_config] site_url: %s", site_url)
    log.info("[powerBI.py][get_ckan_config] api_key: %s", api_key)
    log.info("[powerBI.py][get_ckan_config] storage_path: %s", storage_path)
    log.info("[powerBI.py][get_ckan_config] ssl_cert: %s", ssl_cert)
    
    return site_url, api_key,storage_path,ssl_cert

def get_or_create_counter(self, resource_id, package_id):
        
        counter = Session.query(Contador).filter_by(
            sourceId=resource_id,
            packageId=package_id
        ).first()

        
        # Si ya existe → retornarlo
        if counter:
            return {
                "contVistas": counter.contVistas,
                "contDownload": counter.contDownload,
            }

        if not counter:
            # Caso recurso JSON/no registrado/no datastore: solo devolver valores sin insertar
            return {
                "contVistas": 0,
                "contDownload": 0,
            }
        
        
            
def incrementar_visita(resource_id, package_id):
    counter = self.get_or_create_counter(resource_id, package_id)
    counter.contVistas += 1
    Session.commit()



def main():

    log.info("=== Iniciando creacion del JSON para powerBI ===")

    data={}

    try:

        responses = toolkit.get_action('package_search')({},{})
        package_responses=responses['results']       

        if package_responses:
                    
            registros=responses['count']

            #log.warning(f"[DataJson] get_blueprint powerBI  registros: {registros}")

            data={
                "@context": "https://project-open-data.cio.gov/v1.1/schema/catalog.jsonld",
                "@type": "dcat:Catalog", 
                "conformsTo": "https://project-open-data.cio.gov/v1.1/schema", 
                "describedBy": "https://project-open-data.cio.gov/v1.1/schema/catalog.json",
                'dataset':[],
            }
            url_site=config.get('ckan.site_url')

            
            for package_response in package_responses:

                if package_response.get('type', '').lower() != 'harvest':

                    grupos= package_response.get('groups')
                    organization=package_response.get('organization') 
                    tags=package_response.get('tags') 
                    resources=package_response.get('resources') 

                    #log.error(f"[DataJson] get_blueprint powerBI organization: {organization}")

                    data_dataset={
                        "@type":"dcat:Dataset",
                        "identifier":package_response['id'], 
                        "landingPage":"{}".format(url_site+'/'+package_response.get('type')+'/'+package_response['id']),   
                        "Nombre": package_response.get('title'),
                        "Descripcion": package_response.get('notes'),
                        "Dependencia":organization.get('title') if organization else '',
                        "issued": package_response.get('metadata_created') or '',
                        "modified": package_response.get('metadata_modified') or '',
                        "ciudad": package_response.get('ciudad') or '' ,
                        "departamento":package_response.get('departamento') or '',
                        "Frecuencia_actualizacion":package_response.get('frecuencia_actualizacion') or '',
                        "distribution":[],
                        "keyword":tags,
                        "publisher":{
                            "@type": "{}".format("org:"+ organization.get('title') if organization else ''),
                            "name": "Gobernacion Valle del Cauca"
                        },
                        "contactPoint":{
                                "@type": "vcard:Contact", 
                            "hasEmail": "mailto:wgonzalez@sdp.gov.co", 
                            "fn":  {}
                        },
                        "accessLevel":"Public",
                        'license':{},
                        "theme":[],
                        
                    }

                    if grupos:
                        data_dataset['theme'].append(grupos)
                    
                    title=package_response['title']
                    #log.warning(f"[DataJson] get_blueprint powerBI package_response['title']: {title}")

                    for resource in resources:

                        contador=resource.get('contador')
                        estructura=resource.get('estructura')
                        data_extras=resource.get('data_extra')
                        #log.warning(f"[DataJson] get_blueprint powerBI contador: {contador}")
                        #log.warning(f"[DataJson] get_blueprint powerBI estructura: {estructura}")
                        #log.warning(f"[DataJson] get_blueprint powerBI data_extras: {data_extras}")

                        data_resource= {
                            "@type": "dcat:Distribution",
                            "Url":resource.get('url') or '',  
                            "issued": package_response.get('created') or '',
                            "modified": resource.get('last_modified') or '',                      
                            "filas":estructura.get('filas') if estructura else 0 ,
                            "columnas":estructura.get('columnas') if estructura else 0 ,
                            "vistas":contador.get('visualizaciones') if contador else 0,
                            'descargas':contador.get('descargas') if contador else 0,
                            'categoria': data_extras.get('categoria') if data_extras else '',
                            'fecha_obtencion': data_extras.get('fecha_obtencion') if data_extras else '',
                            'fecha_vencimiento': data_extras.get('fecha_vencimiento') if data_extras else '',
                            'dependiencia': data_extras.get('dependiencia') if data_extras else '',
                            'nivel':data_extras.get('nivel') if data_extras else '',
                        }

                        data_dataset['distribution'].append(data_resource)
                        #log.warning(f"[DataJson] get_blueprint powerBI resources_response: {resource}")
                data['dataset'].append(data_dataset)
        return data    
    except Exception as e:
        log.error(f"[DataJson] Error consultante packages {e}")  
        data={'error':e}
        return data

if __name__ == "__main__":

    data = main()

    # 👇 ESTO es lo que el proceso padre recibirá
    print(json.dumps(data, ensure_ascii=False))

    # Esto solo va al log (opcional)
    logging.info(f"[powerBI] Resultado enviado: {data}")