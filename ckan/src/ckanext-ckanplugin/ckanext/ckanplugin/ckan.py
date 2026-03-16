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



class CkanPligin(DefaultDatasetForm,p.SingletonPlugin):
   
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
            log.warning("[CkanPligin][get_blueprint][track_download] ejecutado")
            helpers.contar_descargas(resource_id,id)   

            return "descarga registrada"
        
        return [estadistica,noticias,analytics_bp, download_bp]
    

        
    def update_config(self, config):

        log.warning("[CkanPligin][update_config] ejecutado")

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
        log.warning("[CkanPligin][package_types] ejecutado") 
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
        log.info("[CkanPligin][before_dataset_create] ejecutado")
        pass

    def after_dataset_create(self,context: Context,  pkg_dict: dict[str, Any]): 
        log.info("[CkanPligin][after_dataset_create] ejecutado")             
        return  pkg_dict 

    def before_dataset_update(self, context, data_dict):
        log.warning("[CkanPligin][before_dataset_update] ejecutado")
        log.warning("[CkanPligin][before_dataset_update] DATA_DICT REAL: %s", data_dict)
        pass

    def after_dataset_update(self,context: Context, pkg_dict: dict[str, Any]):
        log.warning("[CkanPligin][after_dataset_update] ejecutado") 
        log.warning("[CkanPligin][after_dataset_update] DATA_DICT REAL: %s", pkg_dict)       
        return pkg_dict

    def after_dataset_delete(self,context: Context, pkg_dict: dict[str, Any]):
        log.info("[CkanPligin][after_dataset_delete] ejecutado")
        pass        

    def after_dataset_show(self,context: Context, pkg_dict: dict[str, Any]):
        log.info("[CkanPligin][after_dataset_show] ejecutado")
        log.warning("[CkanPligin][after_dataset_show] DATA_DICT REAL: %s", pkg_dict)
        log.warning("CONFIG REAL homepage_style = %s", tk.config.get('ckan.homepage_style'))
        return pkg_dict

    def before_dataset_view(self,pkg_dict: dict[str, Any]):
        log.info("[CkanPligin][before_dataset_view] ejecutado")
        return pkg_dict  

    def before_dataset_search(self,search_params: dict[str, Any]):
        log.info("[CkanPligin][before_dataset_search] ejecutado")
        return search_params   

    def after_dataset_search(self,search_results: dict[str, Any], search_params: dict[str, Any]):
        log.info("[CkanPligin][after_dataset_search] ejecutado")
        return search_results    

    def before_dataset_index(self,pkg_dict: dict[str, Any]):
        log.info("[CkanPligin][before_dataset_index] ejecutado")
        return pkg_dict    
    
    # --- create ---   
    def create(self,entity: Package):
        log.info("[CkanPligin][create] ejecutado")
        pass
    
    # --- delete ---  
    def delete(self,entity: Package):
        log.info("[CkanPligin][delete] ejecutado")
        pass
    
    # --- create ---
    def edit(self,entity: Package):
        log.info("[CkanPligin][edit] ejecutado")
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
        
    
    
    
