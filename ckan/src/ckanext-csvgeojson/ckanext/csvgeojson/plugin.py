import ckan.plugins as p
import ckan.plugins.toolkit as tk
from flask import Blueprint, request, jsonify,current_app
from ckanext.csvgeojson.middleware import registrar_analytics
import logging
from ckan.model import Package
from sqlalchemy import Column, Unicode
import os
import ckanext.csvgeojson.logic.action.resourceRating as rating_action
import ckanext.csvgeojson.logic.action.get as getAction
import ckanext.csvgeojson.logic.action.update as updateAction
import ckanext.csvgeojson.logic.auth.resourceRating as rating_auth
import ckanext.csvgeojson.logic.auth.get as getAuth
import ckanext.csvgeojson.logic.auth.update as updateAuth
import ckanext.csvgeojson.model.package_ext as package_ext
import ckanext.csvgeojson.model as model
import ckanext.csvgeojson.helpers as helpers
from typing import Any
from ckan.types import Context 
from ckan.model import Session
from ckan.plugins.toolkit import DefaultDatasetForm
from ckan.logic.schema import default_create_package_schema
from ckan.logic.schema import default_update_package_schema
from ckan.logic.schema import default_show_package_schema
from ckanext.csvgeojson.services.geojson_converter import GeoJSONConverter  
from ckanext.csvgeojson.views.estadistica import estadistica
from ckanext.csvgeojson.views.noticias import noticias
from ckanext.csvgeojson.views.contador import contador
from flask import current_app



log = logging.getLogger(__name__)



class CSVtoGeoJSON(DefaultDatasetForm,p.SingletonPlugin):
   
    p.implements(p.IConfigurer, inherit=True)   
    p.implements(p.IActions) 
    p.implements(p.IAuthFunctions)
    p.implements(p.ITemplateHelpers)
    p.implements(p.IPackageController)
    p.implements(p.IResourceController)
    p.implements(p.IDatasetForm, inherit=True)
    p.implements(p.IBlueprint)


    def get_blueprint(self):
      
        # Blueprint 2
        download_bp = Blueprint(
            "download_tracker",
            __name__
        )

        analytics_bp = Blueprint("analytics_bp", __name__)

        @analytics_bp.before_app_request
        def registrar_analytics():
            #log.warning("Interceptando request")
            #log.warning(f"Interceptando request.path {request.path}")


            
            if request.path.startswith("/datastore/dump/"):
                resource_id = request.path.split("/")[-1]

                ip = request.remote_addr
                user_agent = request.user_agent.string
                formato = request.args.get("format")
                bom = request.args.get("bom")

                #log.warning(f"Dump datastore detectado {resource_id}")  

                context = {'ignore_auth': True}

                resource = tk.get_action('resource_show')(context, {
                    'id': resource_id
                })

                package_id = resource['package_id']

                #log.warning(f"Dump datastore package_id {package_id}")  

                helpers.contar_descargas(resource_id,package_id) 

        @download_bp.route("/dataset/<id>/resource/<resource_id>/download/<filename>")
        def track_download(id, resource_id, filename):
            log.warning("[CSVtoGeoJSON][get_blueprint][track_download] ejecutado")
            helpers.contar_descargas(resource_id,id)   

            return "descarga registrada"
        
        return [estadistica,noticias,analytics_bp, download_bp]
    

        
    def update_config(self, config):

        log.warning("[CSVtoGeoJSON][update_config] ejecutado")

        #package_ext.extend_package_table() 
        #if not hasattr(Package, 'city'):
        #    Package.city = Column(Unicode, nullable=True)
        #    Package.department = Column(Unicode, nullable=True)
        #    Package.update_frequency = Column(Unicode, nullable=True)

        # Método oficial CKAN
        tk.add_template_directory(config, 'templates')
        tk.add_public_directory(config, 'public')
        tk.add_resource('public','ckanext-csvgeojson')

        
    def package_types(self):
        log.warning("[CSVtoGeoJSON][package_types] ejecutado") 
        return ['dataset']

    def is_fallback(self):
        print("🔥 is_fallback ejecutado")
        return True    

    def create_package_schema(self):
        schema = super().create_package_schema()

        schema.update({
            'city': [
                tk.get_validator('ignore_empty'),
                tk.get_converter('convert_to_extras')
            ],
            'department': [
                tk.get_validator('ignore_empty'),
                tk.get_converter('convert_to_extras')
            ],
            'update_frequency': [
                tk.get_validator('ignore_empty'),
                tk.get_converter('convert_to_extras')
            ],
        })

        return schema


    def update_package_schema(self):
        schema = super().update_package_schema()

        schema.update({
            'city': [
                tk.get_validator('ignore_empty'),
                tk.get_converter('convert_to_extras')
            ],
            'department': [
                tk.get_validator('ignore_empty'),
                tk.get_converter('convert_to_extras')
            ],
            'update_frequency': [
                tk.get_validator('ignore_empty'),
                tk.get_converter('convert_to_extras')
            ],
        })

        return schema


    def show_package_schema(self):
        schema = super().show_package_schema()

        schema.update({
            'city': [
                tk.get_converter('convert_from_extras'),
                tk.get_validator('ignore_missing')
            ],
            'department': [
                tk.get_converter('convert_from_extras'),
                tk.get_validator('ignore_missing')
            ],
            'update_frequency': [
                tk.get_converter('convert_from_extras'),
                tk.get_validator('ignore_missing')
            ],
        })

        return schema
   
    def get_actions(self):
        return {
            'resource_rating_set': rating_action.resource_rating_set,
            'resource_rating_get': rating_action.resource_rating_get,
            'guardar_contador':updateAction.guardar_contador  
        }    

    def get_auth_functions(self):
        return {
            'resource_rating_set': rating_auth.resource_rating_set,
            'resource_rating_get': rating_auth.resource_rating_get,
            'guardar_contador':updateAuth.guardar_contador  
        }

    def get_helpers(self):
        return {
            "obtener_contador_package": helpers.obtener_contador_package,
            "obtener_contador_resource": helpers.obtener_contador_resource,
            "guardar_contador": helpers.guardar_contador,
            "get_featured_noticia":helpers.get_featured_noticia,
            "get_featured_general":helpers.get_featured_general,
            "get_featured_estadistica":helpers.get_featured_estadistica,
            "get_featured_dataset":helpers.get_featured_dataset,
            "get_featured_groups_new":helpers.get_featured_groups_new,
            "contar_visualizacion":helpers.contar_visualizacion,
            "contar_descargas":helpers.contar_descargas,
        } 

    def before_dataset_create(self, context, data_dict):
        log.info("[CSVtoGeoJSON][before_dataset_create] ejecutado")
        pass

    def after_dataset_create(self,context: Context,  pkg_dict: dict[str, Any]): 
        log.info("[CSVtoGeoJSON][after_dataset_create] ejecutado")             
        return  pkg_dict 

    def before_dataset_update(self, context, data_dict):
        log.warning("[CSVtoGeoJSON][before_dataset_update] ejecutado")
        log.warning("[CSVtoGeoJSON][before_dataset_update] DATA_DICT REAL: %s", data_dict)
        pass

    def after_dataset_update(self,context: Context, pkg_dict: dict[str, Any]):
        log.warning("[CSVtoGeoJSON][after_dataset_update] ejecutado") 
        log.warning("[CSVtoGeoJSON][after_dataset_update] DATA_DICT REAL: %s", pkg_dict)       
        return pkg_dict

    def after_dataset_delete(self,context: Context, pkg_dict: dict[str, Any]):
        log.info("[CSVtoGeoJSON][after_dataset_delete] ejecutado")
        pass        

    def after_dataset_show(self,context: Context, pkg_dict: dict[str, Any]):
        log.info("[CSVtoGeoJSON][after_dataset_show] ejecutado")
        log.warning("[CSVtoGeoJSON][after_dataset_show] DATA_DICT REAL: %s", pkg_dict)
        log.warning("CONFIG REAL homepage_style = %s", tk.config.get('ckan.homepage_style'))
        return pkg_dict

    def before_dataset_view(self,pkg_dict: dict[str, Any]):
        log.info("[CSVtoGeoJSON][before_dataset_view] ejecutado")
        return pkg_dict  

    def before_dataset_search(self,search_params: dict[str, Any]):
        log.info("[CSVtoGeoJSON][before_dataset_search] ejecutado")
        return search_params   

    def after_dataset_search(self,search_results: dict[str, Any], search_params: dict[str, Any]):
        log.info("[CSVtoGeoJSON][after_dataset_search] ejecutado")
        return search_results    

    def before_dataset_index(self,pkg_dict: dict[str, Any]):
        log.info("[CSVtoGeoJSON][before_dataset_index] ejecutado")
        return pkg_dict    
    
    # --- create ---   
    def create(self,entity: Package):
        log.info("[CSVtoGeoJSON][create] ejecutado")
        pass
    
    # --- delete ---  
    def delete(self,entity: Package):
        log.info("[CSVtoGeoJSON][delete] ejecutado")
        pass
    
    # --- create ---
    def edit(self,entity: Package):
        log.info("[CSVtoGeoJSON][edit] ejecutado")
        pass        
        
    # --- READ ---      
    def read(self,entity: Package):
        pass
         

     # --- resource_create ---        
    def before_resource_create(self,context: Context, resource: dict[str, Any]):
        pass

    def after_resource_create(self,context: Context, resource: dict[str, Any]):
        pass

    def before_resource_update(self,context: Context, current: dict[str, Any], resource: dict[str, Any]):
        pass

    def after_resource_update(self, context, resource):
        pass     

    def before_resource_delete(self,context: Context, resource: dict[str, Any], resources: list[dict[str, Any]]):
        pass

    def after_resource_delete(self,context: Context, resources: list[dict[str, Any]]):
        pass

    def before_resource_show(self,resource_dict: dict[str, Any]):
        return resource_dict

    def before_resource_search(self,search_params: dict[str, Any]):
        return search_params  

    def after_resource_search(self,context: Context,data_dict: dict[str, Any], search_params: dict[str, Any]):
        return data_dict    
        
    def _guardar_columnas_reales(self, data_dict):

        try:
            log.warning("[CSVtoGeoJSON][_guardar_columnas_reales] ejecutado")  
            
            pkg_id = data_dict.get('id')   
            log.warning("[CSVtoGeoJSON][_guardar_columnas_reales] pkg_id %s",pkg_id)                  

            if not pkg_id:
                log.warning("No hay ID en data_dict")
                return


            pkg = Session.query(Package).get(pkg_id)
            print()
            log.warning("[CSVtoGeoJSON][_guardar_columnas_reales] type %s",type(pkg))
            log.warning("[CSVtoGeoJSON][_guardar_columnas_reales] keys %s",pkg.__table__.columns.keys())
            log.warning("[CSVtoGeoJSON][_guardar_columnas_reales] pkg %s",pkg) 
            
            if not pkg:
                log.warning("No se encontró el PackageExtended con id %s", pkg_id)
                return
            log.warning("[CSVtoGeoJSON][_guardar_columnas_reales] data_dict %s",data_dict)
            
            for campo in ['city', 'department', 'update_frequency']:
                valor = data_dict.get(campo)
                if valor is not None:
                    log.warning("[CSVtoGeoJSON][_guardar_columnas_reales] campo %s valor %s",campo,valor)
                    setattr(pkg, campo, valor)
            
            Session.commit()
            log.warning("[CSVtoGeoJSON][_guardar_columnas_reales] pkg %s",pkg)
            return pkg

        except Exception as e:
            log.error(f"[CSVtoGeoJSON][_guardar_columnas_reales] Error en guardar los campos extras: {e}")
            return data_dict   


    
    
class CSVtoGeoJSONApiPlugin(p.SingletonPlugin):
    
    p.implements(p.IBlueprint)
    #log.info("[CSVtoGeoJSONPlugin] CSVtoGeoJSONApi Cargado con Exito")
    def get_blueprint(self):
        """
        Crea un Blueprint con endpoint manual para convertir CSV a GeoJSON.
        """
        log.info("[CSVtoGeoJSONApiPlugin][get_blueprint][csvgeojson_manual]  ejecutado")

        bp = Blueprint('csvgeojson_manual', __name__)

        @bp.route('/api/3/action/convert_csv_to_geojson', methods=['POST'])
        def convert_csv_to_geojson_endpoint():
            """
            Endpoint manual: recibe resource_id y genera/actualiza GeoJSON.
            """
            try:
                log.info("[CSVtoGeoJSONApiPlugin][csvgeojson_manual][convert_csv_to_geojson_endpoint]  ejecutado")
                payload = request.get_json(force=True) or {}
                log.info(f"[CSVtoGeoJSONPlugin] Payload recibido en endpoint manual: {payload}")

                resource_id = payload.get('resource_id')
                if not resource_id:
                    raise ValidationError({'resource_id': ['Este campo es obligatorio']})
                    
                    
                # Crear context manual
                context = {
                    'model': model,
                    'session': model.Session,
                    'user': c.user or c.author,
                    'ignore_auth': False
                }    
                
                #buscar Paquete asociado
                resource = get_action('resource_show')(context, {'id': resource_id})
                
                # Obtener dataset completo
                package = get_action('package_show')(context, {'id': resource['package_id']})
               
                
                log.info(f"[CSVtoGeoJSONPlugin] package_id encontrado con {resource['id']} : {package['id']}")    

                # Buscar recurso GeoJSON ya existente en el paquete
                geojson_resource = next(
                    (r for r in package['resources'] if r.get('format', '').lower() == 'geojson'),
                    None
                )

                if geojson_resource:
                    #log.info("[CSVtoGeoJSONPlugin] GeoJSON ya existe, será actualizado (ID: %s)", geojson_resource['id'])
                    GeoJSONConverter.convertir_csv_geojson(resource['id'], geojson_resource['id'])  # Pasar ID para update
                else:
                    #log.info("[CSVtoGeoJSONPlugin] No hay GeoJSON, creando nuevo")
                    GeoJSONConverter.self.convertir_csv_geojson(resource['id'])  

                return jsonify({"success": True, "message": f"GeoJSON generado para recurso {resource_id}"})

            except ValidationError as ve:
                log.error(f"[CSVtoGeoJSONPlugin] Error de validación: {ve}")
                return jsonify({"success": False, "error": str(ve)}), 400

            except Exception as e:
                log.error(f"[CSVtoGeoJSONPlugin] Error en conversión manual: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

            # CKAN requiere lista de blueprints
        return [bp]

    
class ContadorPlugin(p.SingletonPlugin):
    p.implements(p.IBlueprint)

    log.info("[CSVtoGeoJSON][ContadorPlugin] Cargado con Exito")
    bp = Blueprint("ckanext_counter", __name__)

    @bp.after_app_request
    def contar(response):

        log.warning(f"[CSVtoGeoJSON][Contador][contar] Ejecutado")

        if response.status_code != 200:
            return response

        endpoint = request.endpoint

        if endpoint in ["resource.download", "resource.view"]:

            
            view_args = request.view_args or {}
            resource_id = view_args.get("id") 
            package_id = view_args.get("package_id") 

            if resource_id and not package_id:
                resource = tk.get_action("resource_show")(
                    {"ignore_auth": True},
                    {"id": resource_id}
                )
                package_id = resource.get("package_id") or ''
            

            if resource_id:
                tipo = "download" if endpoint == "resource.download" else "view"

                helpers = tk.get_helpers()
                helpers["guardar_contador"](package_id,resource_id, tipo)

        return response

    