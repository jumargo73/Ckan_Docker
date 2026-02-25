from ckan.plugins import SingletonPlugin, IDatasetForm, implements, IPackageController, IResourceController
from ckan.plugins import toolkit
from ckan.plugins.interfaces import IResourceView, IConfigurer, IBlueprint
from flask import Blueprint,request
import json, logging,os,  mimetypes
from datetime import datetime, date
import ckan.logic as logic
import ckan.model as model
from model import Session, Resource,Package,PackageExtra,Contadores
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
import os

TRUTHY = {'true', 'on', '1', 'si', 'sí'}

log = logging.getLogger(__name__)

class CSVtoGeoJSONDatasetResourcePlugin(SingletonPlugin):
    implements(IResourceController)
    implements(IPackageController)
    implements(IResourceController)

   
    
    log.info("[CSVtoGeoJSONPlugin] CSVtoGeoJSONDatasetResourcePlugin Cargado con Exito")
    
    
    # --- resource_create ---        
    def before_resource_create(self,context: Context, resource: dict[str, Any]):
        pass

    def after_resource_create(self,context: Context, resource: dict[str, Any]):
        pass
        
    # --- dataset_create ---     
    def after_dataset_create(self,context: Context,  pkg_dict: dict[str, Any]):
        
        return pkg_dict
    
    # --- resource_update ---    

    def before_resource_update(self,context: Context, current: dict[str, Any], resource: dict[str, Any]):
        pass

    def after_resource_update(self, context, resource):

        
        log.warning("[CSVtoGeoJSONPlugin] after_resource_update ejecutado")
        
        # Procesar solo CSV
        if resource.get('format', '').lower() == 'csv':

            # Obtener dataset completo
            package = toolkit.get_action('package_show')(context, {'id': resource['package_id']})
            
            
            # Buscar recurso GeoJSON ya existente en el paquete
            geojson_resource = next(
                (r for r in package['resources'] if r.get('format', '').lower() == 'geojson'),
                None
            )

            if geojson_resource:
                log.warning("[CSVtoGeoJSONPlugin] GeoJSON ya existe, será actualizado (ID: %s)", geojson_resource['id'])
                GeoJSONConverter.convertir_csv_geojson(resource['id'], geojson_resource['id'])  # Pasar ID para update
            else:
                log.warning("[CSVtoGeoJSONPlugin] No hay GeoJSON, creando nuevo")
                GeoJSONConverter.convertir_csv_geojson(resource['id'])

    
    # --- dataset_update ---
    
    def after_dataset_update(self,context: Context, pkg_dict: dict[str, Any]):

        log.info("[CSVtoGeoJSONPlugin] after_dataset_update ejecutado")

        if context.get('skip_sello_excelencia'):
            return    

        
        # Leer el valor del checkbox desde el formulario
        val = toolkit.request.form.get('sello_excelencia') or pkg_dict.get('sello_excelencia')

        
        # Determinar si está marcado
        is_checked = bool(val and str(val).strip().lower() in TRUTHY)

        #log.info("[CSVtoGeoJSONPlugin] after_dataset_update tiene sello , %s",is_checked) 

        # Traer el dataset actual
        pkg_id = pkg_dict.get('id') or pkg_dict.get('name')
        if not pkg_id:
            return

        pkg = toolkit.get_action('package_show')({'user': context.get('user')}, {'id': pkg_id})
        extras = pkg.get('extras', [])

        # Quitar valor previo si existe
        extras = [e for e in extras if e.get('key') != 'sello_excelencia']

        # Guardar cambios
        if is_checked:
            extras.append({'key': 'sello_excelencia', 'value': 'true'})

        # ⚠️ Pasar bandera para que el evento no se dispare otra vez
        new_context = dict(context, skip_sello_excelencia=True)
        toolkit.get_action('package_patch')(new_context, {'id': pkg_id, 'extras': extras})

        #log.info("[CSVtoGeoJSONPlugin] after_dataset_update Dataset Marcado con Exito")          
        

    # --- resource_delete ---
        
    def before_resource_delete(self,context: Context, resource: dict[str, Any], resources: list[dict[str, Any]]):
        pass

    def after_resource_delete(self,context: Context, resources: list[dict[str, Any]]):
        pass

    # --- dataset_delete ---
    def after_dataset_delete(self,context: Context, pkg_dict: dict[str, Any]):
        pass
    
    # --- resource_show ---
    
    def before_resource_show(self,resource_dict: dict[str, Any]):
        return resource_dict

    def before_dataset_show(self,context: Context, pkg_dict: dict[str, Any]):
        return pkg_dict
    
    
    # --- dataset_show ---   
    def after_dataset_show(self,context: Context, pkg_dict: dict[str, Any]):

        #log.info("[CSVtoGeoJSONPlugin] after_dataset_show ejecutado")
        ##log.info("[SelloExcelenciaView]  fter_dataset_show pkg_dict devuelto: %s", json.dumps(pkg_dict, indent=2, ensure_ascii=False))    
        return pkg_dict
        
    def before_dataset_view(self,pkg_dict: dict[str, Any]):
        return pkg_dict  
        
    # --- dataset_search ---    
    def before_dataset_search(self,search_params: dict[str, Any]):
        log.info("[CSVtoGeoJSONPlugin] before_dataset_search ejecutado")
        return search_params    
    
    def before_resource_search(self,search_params: dict[str, Any]):
        log.info("[CSVtoGeoJSONPlugin] before_resource_search ejecutado")
        return search_params  

    def after_dataset_search(self,search_results: dict[str, Any], search_params: dict[str, Any]):
        log.info("[CSVtoGeoJSONPlugin] after_dataset_search ejecutado")
        try:
            # 1️⃣ Obtener contadores desde tu acción
            #contador_action = toolkit.get_action('contador_get')
            context = {
                'model': model,
                'session': model.Session,
                'user': toolkit.g.user or toolkit.config.get('ckan.site_id')
            }
            
            contadores = self.contador_get()
            
            
            #log.info(f"[CSVtoGeoJSONPlugin] after_dataset_search contadores {contadores}")

            # 2️⃣ Optimizar acceso mapeando por resource_id
            contador_map = {c['resource_id']: c for c in contadores}

            # 3️⃣ Iterar los datasets y agregar contador a cada recurso
            for dataset in search_results.get('results', []):

                package_id=dataset.get('id') if dataset else ''

                consolidado=self.get_consolidado_contador(package_id)

                dataset['consolidado']=consolidado if consolidado else {}

                log.info(f"[CSVtoGeoJSONPlugin] after_dataset_search package['id']= {package_id} consolidado {consolidado}")
               
                for resource in dataset.get('resources', []):
                    #log.info(f"[CSVtoGeoJSONPlugin] after_dataset_search resource['id']= {resource['id']}")
                    rid = resource.get('id')
                    filas_columnas_map=self.get_filas_columnas(rid,context)
                    data_extra=self.get_extras(rid)
                    resource['contador'] = contador_map.get(rid, None)
                    resource["estructura"] = filas_columnas_map
                    resource["data_extra"] =data_extra

        except Exception as e:
            log.error(
                f"[CSVtoGeoJSONPlugin] Error after_dataset_search: {str(e)}"
            )

        return search_results
        
    
    def after_resource_search(self,context: Context,data_dict: dict[str, Any], search_params: dict[str, Any]):
        
        return data_dict
       
    
    # --- dataset_index ---   
    
    def before_dataset_index(self,pkg_dict: dict[str, Any]):
        return pkg_dict
    
    
    # --- create ---   
    def create(self,entity: model.Package):
        pass
    
    # --- delete ---  
    def delete(self,entity: model.Package):
        pass
    
    # --- create ---
    def edit(self,entity: model.Package):
        pass        
        
    # --- READ ---      
    def read(self,entity: model.Package):
        pass


    def get_extras(self,id):

        
        try:

            #log.info("[CSVtoGeoJSONPlugin] get_extras ejecutado")

            resource_model = Session.query(Resource).filter(
                Resource.format.ilike('PDF'),
                Resource.id == id
            ).first()

            if not resource_model:
                #log.warning("[DataJson] get_extras No se encontró recurso con ID: %s", id)
                return {
                    "resource_id":id,
                    "categoria":"",
                    "fecha_obtencion":"",
                    "fecha_vencimiento":"",
                    "dependiencia":"",
                    "nivel":"",
                }  

            extras = {}

            if resource_model.extras:
                if isinstance(resource_model.extras, str):
                    try:
                        extras = json.loads(resource_model.extras)
                    except Exception as e1:
                            log.error(f"[DataJson] Error id {id} {e1}")
                            return {
                                "resource_id":id,
                                "categoria":"",
                                "fecha_obtencion":"",
                                "fecha_vencimiento":"",
                                "dependiencia":"",
                                "nivel":"",
                                "error": str(e1)
                            }  
                elif isinstance(resource_model.extras, dict):
                    extras = resource_model.extras

            if extras.get('type')=="sello_excelencia":
                return {
                    "resource_id":id,
                    "categoria":extras.get('type'),
                    "fecha_obtencion":extras.get('fecha_obtencion'),
                    "fecha_vencimiento":extras.get('fecha_vencimiento'),
                    "dependiencia":extras.get('owner_org'),
                    "nivel":extras.get('nivel'),
                    "error": ""
                }        
            else:
                return {
                    "resource_id": id,
                    "categoria":"",
                    "fecha_obtencion":"",
                    "fecha_vencimiento":"",
                    "dependiencia":"",
                    "nivel":"",
                    "error": "No tiene Sello de Excelencia"
                }  
        
        except Exception as e:
            log.error(f"[DataJson] Error id {id} {e}")
            return [
                {
                    "resource_id":id,
                    "categoria":"",
                    "fecha_obtencion":"",
                    "fecha_vencimiento":"",
                    "dependiencia":"",
                    "nivel":"",
                    "error":str(e)
                }
            ]

    def get_filas_columnas(self,id,context):
        try:
            #log.info("[CSVtoGeoJSONPlugin] get_filas_columnas ejecutado")
            datastore_response = toolkit.get_action('datastore_search')(context,{'id': id})
            if datastore_response:
                columnas = len(datastore_response.get("fields", []))
                filas = datastore_response.get("total", 0)  
                #log.warning(f"[CSVtoGeoJSONPlugin] get_filas_columnas con id={id}: filas={filas}, columnas={columnas}")
                return{
                        "resource_id": id,
                        "filas": filas,
                        "columnas": columnas,
                        "error": ""
                    }
                
                
            else:
                #log.warning(f"[CSVtoGeoJSONPlugin] get_filas_columnas con id={id}: filas=0,columnas=0")
                return {
                        "resource_id": id,
                        "filas": 0,
                        "columnas": 0,
                        "error": str(datastore_response)
                    }
                
               

        except Exception as e:
            log.error(f"[CSVtoGeoJSONPlugin] get_filas_columnas con id {id} error={e}")
            return {
                    "resource_id": id,
                    "filas": 0,
                    "columnas": 0,
                    "error": str(e)
                }
            
           
    def get_consolidado_contador(selft,package_id): 
                
        """
            Devuelve el consolidado de las vistas y descargas de los recursos.
        """

        log.info("[CSVtoGeoJSONPlugin] get_consolidado_contador ejecutado")
    
        session = model.Session

        vistas=0
        descargas=0

        rows = Session.query(Contadores).filter(
                Contadores.package_id == package_id
            ).all()

       
        for row in rows:
            vistas+=row.contVistas
            descargas+=row.contDownload
            log.info(f"[CSVtoGeoJSONPlugin] get_consolidado_contador vistas {vistas} descargas {descargas}")

        
        log.info(f"[CSVtoGeoJSONPlugin] get_consolidado_contador registro {rows}")

        return{
                "visualizaciones": vistas if vistas else 0,
                "descargas": descargas if descargas else 0,
                "package_id": row.packageId,
            }
          


              

    def contador_get(self):
        """
        Devuelve los contadores almacenados en la tabla personalizada.
        """

        #log.info("[CSVtoGeoJSONPlugin] contador_get ejecutado")
    
        session = model.Session

        rows = session.query(Contadores).all()

        #log.info(f"[CSVtoGeoJSONPlugin] contador_get registro {rows}")

        return [
            {
                "resource_id": row.source_Id,
                "visualizaciones": row.contVistas,
                "descargas": row.contDownload,
                "package_id": row.package_Id,
            }
            for row in rows
        ]   
       
    
class SelloExcelenciaView(SingletonPlugin):
   
    implements(IBlueprint)
    implements(IConfigurer)
    
    log.info("[SelloExcelenciaView]  Cargado con Exito")
    
    def update_config(self, config):
        
        log.info("[SelloExcelenciaView] update_config ejecutado")

        # Ruta absoluta de la carpeta templates de este plugin
        template_path = os.path.join(os.path.dirname(__file__), 'templates')
        #log.info(f"[SelloResourcePlugin] Buscando templates en: {template_path}")

         # Archivos estáticos (public)
        public_path = os.path.join(os.path.dirname(__file__), "public")
        #log.info(f"[SelloResourcePlugin] Buscando images en: {public_path}")

        # Verificar que los archivos existan
        for root, dirs, files in os.walk(template_path):
            for f in files: 
                continue              
                #log.info(f"[SelloExcelenciaView] Template detectado: {os.path.join(root, f)}")

        # Verificar que los archivos existan
        for root, dirs, files in os.walk(public_path):
            for f in files:  
                continue              
                #log.info(f"[SelloExcelenciaView] Imagenes detectadas: {os.path.join(root, f)}")
      
        # Método oficial CKAN
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')

        # Método manual como respaldo
        if 'extra_template_paths' in config:
            config['extra_template_paths'] += ':' + template_path
        else:
            config['extra_template_paths'] = template_path
    
    def get_blueprint(self):    
        
        sello_bp = Blueprint("sello_excelencia", __name__, template_folder='templates')

        @sello_bp.route("/sello/listar")
        def listar_sellos():

            #log.info("[SelloExcelenciaView]  listar_sellos ejecutado")
            
            '''context = {'user': toolkit.c.user or toolkit.config.get('ckan.site_id')}

            #log.info("[SelloExcelenciaView]  context: %s", json.dumps(context, indent=2, ensure_ascii=False))

            # aquí validas si tiene permisos, por ejemplo acceso admin a dataset
            try: 
                toolkit.check_access('package_update', context)
                #log.info("[SelloExcelenciaView]  Con Acceso")
                can_edit = True
            except logic.NotAuthorized:
                #log.info("[SelloExcelenciaView]  Sin acceso")
                can_edit = False'''

            can_edit = True    
            #log.info("[SelloExcelenciaView]  acceso: true")

            # URL base del portal CKAN
            base_url = config.get('ckan.site_url', '').rstrip('/')
            #log.info("[SelloExcelenciaView]  base_url: %s", base_url)

            # Consultar todos los recursos PDF
            recursos = Session.query(Resource).filter(
                Resource.format.ilike('PDF')
            ).all()
    
            
            sellos = []
            
            for r in recursos:
                #print(r.id, r.name, r.format, r.url, r.extras)
                # Revisar si es un sello según el extra 'type'                
                extras = {}
                if r.extras:
                    if isinstance(r.extras, str):
                        try:
                            extras = json.loads(r.extras)
                        except Exception as e:
                            log.error(f"[SelloExcelenciaView]  error {e}")
                            extras = {}                           
                    elif isinstance(r.extras, dict):
                        extras = r.extras
                        #log.info("[SelloExcelenciaView]  listar_sellos extras dict Encontrado: %s", json.dumps(extras, indent=2, ensure_ascii=False))

                

                if extras.get('type') != 'sello_excelencia':
                    continue

                # Construir nombre del archivo
                archivo = r.url.split('/')[-1] if r.url else ''
                url_descarga = f"{base_url}/dataset/{r.package_id}/resource/{r.id}/download/{archivo}"

                # Logs de depuración
                #log.info("[SelloExcelenciaView]  package_id: %s", r.package_id)
                #log.info("[SelloExcelenciaView]  resource_id: %s", r.id)
                #log.info("[SelloExcelenciaView]  archivo: %s", archivo)
                #log.info("[SelloExcelenciaView]  url_descarga: %s", url_descarga)

                
                # Agregar a la lista
                sellos.append({
                    "id": r.id,
                    "package_id": r.package_id,
                    'title': r.name,
                    'description': r.description,
                    'pdf_url': url_descarga,
                    'fecha': r.created,
                    'categoria': extras.get('type'),
                    'fecha_obtencion': extras.get('fecha_obtencion'),
                    'fecha_vencimiento': extras.get('fecha_vencimiento'),
                    'dependiencia': extras.get('owner_org'),
                    'nivel': extras.get('nivel')
                })
            
            # ---------------------------
            # Paginación
            # ---------------------------
            per_page = 10  # cantidad de sellos por página
            page = int(request.args.get("page", 1))  # ?page=2
            total = len(sellos)

            # calcular inicio y fin
            start = (page - 1) * per_page
            end = start + per_page

            # recorte de la lista
            sellos_paginados = sellos[start:end]

            # total de páginas
            total_pages = (total + per_page - 1) // per_page
                    
            # 🔹 Log completo de la lista sellos
            #log.info("Lista completa de sellos: %s", sellos)

            return toolkit.render('sello/listar.html', {'sellos': sellos_paginados,'page':page,'total_pages':total_pages, 'can_edit': can_edit})

        @sello_bp.route('/sello/edit/<id>')
        def sello_edit(id):

            
            log.info("[SelloExcelenciaView] sello_edit Ejecutado") 
           
            # 🔹 Log completo de la lista sellos
            #log.info("[SelloExcelenciaView] sello_edit id: %s", id)

            context = {'model': model, 'session': model.Session,'user': toolkit.c.user or toolkit.config.get('ckan.site_id')}
            
            organizations=self.listar_organizaciones()

            #log.info("[SelloExcelenciaView] sello_edit organizations: %s", json.dumps(organizations, indent=2, ensure_ascii=False))
           
 
            sello = self.get_sello(id,context)  # lógica de obtener el recurso
            
            #log.info("[SelloExcelenciaView] sello_edit sello: %s", sello)

            extras = {}
            if sello.extras:
                if isinstance(sello.extras, str):
                    try:
                        extras = json.loads(sello.extras)
                    except Exception:
                        log.error(f"[SelloExcelenciaView]  error {e}")
                        extras = {}                           
                elif isinstance(sello.extras, dict):
                    extras = sello.extras
            
            #log.info("[SelloExcelenciaView]  listar_sellos extras dict Encontrado: %s", json.dumps(extras, indent=2, ensure_ascii=False))

            package = toolkit.get_action('package_show')(
                    context,
                    {'id': sello.package_id}
                )
            
            #log.info("[SelloExcelenciaView] sello_edit package: %s", json.dumps(package, indent=2, ensure_ascii=False))
                        
            #log.info("[SelloExcelenciaView] sello_edit organizacion_id: %s", package['organization']['id'])
            
            entidad = toolkit.get_action('organization_show')(
                    context,
                    {'id': package['organization']['id']}
                )

            #log.info("[SelloExcelenciaView] sello_edit organization: %s", json.dumps(entidad, indent=2, ensure_ascii=False))
              

            # Si es GET, mostrar formulario
            return toolkit.render(
                'sello/resource_form.html',
                {
                    'package': package,
                    'csrf_field': h.csrf_input(),
                    'organizations':organizations,
                    'resource':sello,
                    'entidad':entidad,
                    'extras':extras
                }
            )

        @sello_bp.route('/sello/update/<id>', methods=['POST'])   
        def update_sello_resource(id):

            context = {'model': model, 'session': model.Session, 'user': toolkit.c.user}
            # 1️⃣ Recibir los textos
            package_id = toolkit.request.form.get('package_id')
            nombre = toolkit.request.form.get('name')
            nombre_limpio = re.sub(r'\s+', '_', nombre.strip())
            extension = toolkit.request.form.get('format')
            description = toolkit.request.form.get('description')
            owner_org = toolkit.request.form.get('owner_org')
            fecha_obtencion = toolkit.request.form.get('fecha_obtencion')
            nivel = toolkit.request.form.get('nivel')
            
            # 2️⃣ Recibir el archivo
            archivo = toolkit.request.files.get('upload')
            file_path = None
        
            # 3️⃣ Aquí haces lo que necesites con los datos, por ejemplo:
            
            #log.info("[SelloExcelenciaView]  update_sello_resource Package ID:: %s", package_id)
            #log.info("[SelloExcelenciaView]  update_sello_resource Nombre: %s", nombre)
            #log.info("[SelloExcelenciaView]  update_sello_resource Extensión: %s", extension)
            #log.info("[SelloExcelenciaView]  update_sello_resource Descripción: %s", description)
            #log.info("[SelloExcelenciaView]  update_sello_resource owner_org: %s", owner_org) 
            #log.info("[SelloExcelenciaView]  update_sello_resource fecha_obtencion: %s", fecha_obtencion)   
            #log.info("[SelloExcelenciaView]  update_sello_resource nivel: %s", nivel)                   
        
            resource = toolkit.get_action('resource_show')({'user': toolkit.c.user}, {'id': id})
            package = toolkit.get_action('package_show')({'user': toolkit.c.user}, {'id': resource['package_id']})
            
            organizacion = toolkit.get_action('organization_show')({'user': toolkit.c.user}, {'id': owner_org})
            
            file_name=None

            nombre_archivo = "{}.{}".format(nombre_limpio,extension)
            
            
            if archivo:
                file_name = nombre_archivo = "{}.{}".format(nombre_limpio,extension)
                #nombre_archivo = archivo.filename

                # 1 Crear Recurso
                resource_dict= {
                    'package_id':package['id'] ,
                    'name':nombre,
                    'url':file_name,  # URL temporal,
                    'format':extension,
                    'description':description
                }
            else:
                # 1 Crear Recurso
                resource_dict= {
                    'package_id':package['id'] ,
                    'name':nombre,
                    'url':nombre_archivo,  # URL temporal,                    
                    'format':extension,
                    'description':description
                }

            #log.info("[SelloExcelenciaView]  update_sello_resource resource_dict: %s", resource_dict)
            
            #Crear Recurso
            result = self.save_sello_excelencia(resource_dict,file_name,archivo,context,organizacion,resource)
            
            #toolkit.h.flash_success("Recurso creado correctamente")
            return toolkit.redirect_to(toolkit.h.url_for('sello_excelencia.listar_sellos'))
                

            

        
        @sello_bp.route('/sello/delete/<id>', methods=['POST'])
        def sello_delete(id):

            log.info("[SelloExcelenciaView]  sello_delete ejecutado")

            context = {
                "model": model,
                "session": model.Session,
                "user": toolkit.c.user  # usuario actual
            }

            data_dict = {"id": id}

            try:
                toolkit.get_action("resource_delete")(context, data_dict)
                toolkit.h.flash_success("Recurso eliminado correctamente.")
            except toolkit.ObjectNotFound:
                toolkit.h.flash_error("El recurso no existe.")
            except toolkit.NotAuthorized:
                toolkit.h.flash_error("No tienes permisos para eliminar este recurso.")

            return toolkit.redirect_to(toolkit.h.url_for("sello_excelencia.listar_sellos"))         
            
            
        
        @sello_bp.route('/sello/resource_form/<package_id>', methods=['GET', 'POST'])
        def new_sello_resource(package_id):            
    
            try:
                
                log.info("[SelloExcelenciaView]  new_sello_resource ejecutado")
                
                # Obtener el dataset
                package = toolkit.get_action('package_show')(
                    {'ignore_auth': True},
                    {'id': package_id}
                )


                organizations=self.listar_organizaciones()
                
                if not package:
                    h.flash_error("Dataset no encontrado")
                    return h.redirect_to('home.index')

                # Si es POST, CKAN ya valida automáticamente el CSRF
                if request.method == 'POST':
                    
                    context = {'model': model, 'session': model.Session, 'user': toolkit.c.user}
                    # 1️⃣ Recibir los textos
                    package_id = toolkit.request.form.get('package_id')
                    nombre = toolkit.request.form.get('name')
                    nombre_limpio = re.sub(r'\s+', '_', nombre.strip())
                    extension = toolkit.request.form.get('format')
                    description = toolkit.request.form.get('description')
                    owner_org = toolkit.request.form.get('owner_org')
                    fecha_obtencion = toolkit.request.form.get('fecha_obtencion')
                    nivel = toolkit.request.form.get('nivel')
                    application=None;
                    
                    # 2️⃣ Recibir el archivo
                    archivo = toolkit.request.files.get('upload')
                    file_path = None
                
                    # 3️⃣ Aquí haces lo que necesites con los datos, por ejemplo:
                    
                    #log.info("[SelloExcelenciaView]  new_sello_resource Package ID:: %s", package_id)
                    #log.info("[SelloExcelenciaView]  new_sello_resource Nombre: %s", nombre)
                    #log.info("[SelloExcelenciaView]  new_sello_resource Extensión: %s", extension)
                    #log.info("[SelloExcelenciaView]  new_sello_resource Descripción: %s", description)
                    #log.info("[SelloExcelenciaView]  new_sello_resource owner_org: %s", owner_org) 
                    #log.info("[SelloExcelenciaView]  new_sello_resource fecha_obtencion: %s", fecha_obtencion)   
                    #log.info("[SelloExcelenciaView]  new_sello_resource nivel: %s", nivel)                   
                
                  

                    package = toolkit.get_action('package_show')({'user': toolkit.c.user}, {'id': package_id})
                    organizacion = toolkit.get_action('organization_show')({'user': toolkit.c.user}, {'id': owner_org})
                    
                    
                    
                    if archivo:

                        file_name = nombre_archivo = "{}.{}".format(nombre_limpio,extension)
                        #nombre_archivo = archivo.filename

                        if extension.lower()=='csv':
                            extension='PDF'
                            application='application/pdf'
                            
                        # 1 Crear Recurso
                        resource_dict= {
                            'package_id':package['id'] ,
                            'name':nombre,
                            'url':file_name,  # URL temporal,
                            'format':extension,
                            "mediaType": application,
                            'description':description
                        }

                        #log.info("[SelloExcelenciaView]  new_sello_resource resource_dict: %s", resource_dict)
                        
                       
                        
                        #Crear Recurso
                        result = self.save_sello_excelencia(resource_dict,file_name,archivo,context,organizacion)
                        
                        #toolkit.h.flash_success("Recurso creado correctamente")
                        return toolkit.redirect_to(toolkit.h.url_for('sello_excelencia.listar_sellos'))
                      
                    
                # Si es GET, mostrar formulario
                return toolkit.render(
                    'sello/resource_form.html',
                    {
                        'package': package,
                        'csrf_field': h.csrf_input(),
                        'organizations':organizations
                    }
                )
            except logic.NotFound:
                log.error(f"[SelloExcelenciaView]  error {logic.NotFound}")
                # Handle the case where the package is not found
                return h.redirect_to('home.index')

        # Intercepta la edición de datasets
        @sello_bp.app_context_processor
        def inject_sello_extras():

            log.info("[SelloExcelenciaView]  injenject_sello_extras Ejecutado")
           
            if request.endpoint == 'dataset.edit':
                try:
                    
                    dataset_id = request.view_args.get('id')
                    pkg = model.Session.query(model.Package).options(joinedload(model.Package._extras)).filter_by(name=dataset_id).first()
                    extras_dict = {}
                    if pkg:
                        #log.info("[SelloExcelenciaView]  injenject_sello_extras pkg._extras: %s", pkg._extras)
                        for key, extra_obj in pkg._extras.items():
                            extras_dict[key] = extra_obj.value  # extra_obj.value es el valor que queremos
                        return dict(_extras=extras_dict)
                except Exception as e:                        
                    log.error("[SelloExcelenciaView]  error: %s", e)
                    return dict(_extras={})
            return dict()
            
        return sello_bp
    


    def get_sello(self, id,context):

        
        log.info("[SelloExcelenciaView]  get_sello Ejecutado")
        
        resource = Session.query(Resource).filter(
            Resource.format.ilike('PDF'),
            Resource.id == id
        ).first()
        #resource = toolkit.get_action('resource_show')(context, {'id': id})
        return resource

    def sello_edit(self, id,context):
        log.info("[SelloExcelenciaView]  sello_edit Ejecutado")
        resource = toolkit.get_action('resource_show')(context, {'id': id})
        return resource
        


    def sello_delete(self, id,context):
        log.info("[SelloExcelenciaView]  sello_delete Ejecutado")
        resource = toolkit.get_action('resource_delete')(context, {'id': id})
        return resource

    
    def save_sello_excelencia(self, resource_dict,file_name,archivo,context,organizacion,resource=None):
        
        
        try:
            log.info("[SelloExcelenciaView]  save_sello_excelencia Ejecutado")

            """
            Crea un recurso placeholder y luego actualiza con extras y datos reales.
            """
            storage_path = config.get("ckan.storage_path")
            
            #package_id = package['id']
            
            #data_dict = dict(toolkit.request.form)

            # 1 Crear Recurso
            '''resource_dict= {
                'package_id':package_id ,
                'name':data_dict.get('name'),
                'url':file_name,  # URL temporal,
                'format':data_dict.get('format'),
                'description':data_dict.get('description')
            }'''


            if resource:
                # Actualizar recurso existente
                resource_dict["id"] = resource["id"]
                action = "resource_update"
                resource = toolkit.get_action('resource_update')(context, resource_dict)
                #log.info("[SelloExcelenciaView]  save_sello_excelencia resource update: %s", json.dumps(resource, indent=2, ensure_ascii=False))

            else:
                # Crear nuevo recurso
                action = "resource_create"
            
                resource = toolkit.get_action('resource_create')(context, resource_dict)
                #log.info("[SelloExcelenciaView]  save_sello_excelencia create: %s", json.dumps(resource, indent=2, ensure_ascii=False))

           
            
            
            
            resource_id = resource['id']
            
            ##log.info("[SelloExcelenciaView]  crear_sello_excelencia resource_id: %s", resource_id)
            
            nuevo_nombre = resource_id[6:] 
            ##log.info("[SelloExcelenciaView]  crear_sello_excelencia nuevo_nombre: %s", nuevo_nombre)
                      
            
           
            # 2 Calcular ruta destino CKAN
            geojson_res_id = resource_id # UUID del recurso
            subdir = os.path.join(geojson_res_id[0:3], geojson_res_id[3:6]) # Creacion Arbol donde va a qUUID del recurso
            resource_path = os.path.join(storage_path, "resources")    
            dest_dir = os.path.join(resource_path,subdir)
            os.makedirs(dest_dir, exist_ok=True)
            

            # 3 Guardar Archivo
            nuevo_nombre = resource_id[6:] 
            dest_path = os.path.join(dest_dir, nuevo_nombre)
            
            if file_name is not None:
                archivo.save(dest_path)


            # 4 Obtener size, last_modified y mimetype
            size = os.path.getsize(dest_path)
            last_modified = datetime.fromtimestamp(os.path.getmtime(dest_path))
            mimetype, encoding = mimetypes.guess_type(archivo.filename, strict=True)
            
            
            # 1. Obtener el recurso completo
            #resource = toolkit.get_action('resource_show')(context, {'id': resource_id})

            # 5. Actualizar solo los campos que quieras cambiar
            resource['url_type'] = 'upload'
            resource['size'] = size
            resource['mimetype'] = mimetype
            resource['last_modified'] = last_modified.isoformat()

            # 6 Actualizar URL y otros campos

            '''resource_dict = {
                'id': resource_id,
                'url_type': 'upload',
                'url':file_name,
                'size': size,
                'mimetype': mimetype,
                'last_modified': last_modified.isoformat()
            }'''
            
            
            # 6. Mandar el recurso completo a update
            updated_resource = toolkit.get_action('resource_update')(context, resource)
            #updated_resource = toolkit.get_action('resource_update')(context, resource_dict)

            #log.info("[SelloExcelenciaView]  save_sello_excelencia resource update 1: %s", json.dumps(updated_resource, indent=2, ensure_ascii=False))

    
            # 5 Marcar Etiqueta de Sello
            response=self.marcar_recurso_sello(resource_id,organizacion)
            #log.info("[SelloExcelenciaView]  Recurso Guardado con Exito")
            return True
        except Exception as e:
            log.error("[SelloExcelenciaView]  Error al guardar el archivo: $s",e)           
            return  False

    def marcar_recurso_sello(self, resource_id,organizacion):

        try:

            log.info("[SelloExcelenciaView]  marcar_recurso_sello Ejecutado")

            # El context suele incluir al usuario (puede ser sysadmin)
            context = {
                'model': model,
                'session': model.Session,
                'user': toolkit.c.user  # o el nombre de un usuario válido
            }

            # Obtener el recurso actual
            get_resource = toolkit.get_action('resource_show')            
            resource = get_resource({'ignore_auth': True}, {'id': resource_id})

            #log.info("[SelloExcelenciaView]  marcar_recurso_sello resource show: %s", resource)


            #owner_org = toolkit.request.form.get('owner_org')
            #organizacion = toolkit.get_action('organization_show')(context, {'id': owner_org})
        
            fecha_obtencion = toolkit.request.form.get('fecha_obtencion')
            #log.info("[SelloExcelenciaView]  marcar_recurso_sello fecha_obtencion: %s", fecha_obtencion) 

            try:
                
                # Normalizar la fecha: convertir solo si es str
                if isinstance(fecha_obtencion, str):
                    fecha_dt = datetime.strptime(fecha_obtencion, "%Y-%m-%d")
                elif isinstance(fecha_obtencion, datetime):
                    fecha_dt = fecha_obtencion
                elif isinstance(fecha_obtencion, date):
                    # Convertir date -> datetime para poder sumar el relativedelta sin problemas
                    fecha_dt = datetime.combine(fecha_obtencion, datetime.min.time())
                else:
                    log.error(">>> Tipo no soportado: %s", fecha_vencimiento)
                    raise ValueError(f"Tipo no soportado ({type(fecha_obtencion)}) para fecha_obtencion")
  
                # Sumar 1 año
                fecha_vencimiento = (fecha_dt + relativedelta(years=1)).date()
                log.info("[SelloExcelenciaView] fecha_obtencion: %s → fecha_vencimiento: %s", fecha_dt.date(), fecha_vencimiento)
            except Exception as e:
                log.error(">>> ERROR calculando fecha_vencimiento: %s", e)

            
            nivel = toolkit.request.form.get('nivel')
            #log.info("[SelloExcelenciaView]  marcar_recurso_sello nivel: %s", nivel)  



            # Agregar la bandera como campo plano (CKAN lo guarda en extras)
            resource['type'] = 'sello_excelencia'
            resource['fecha_obtencion'] = fecha_obtencion
            resource['fecha_vencimiento'] = fecha_vencimiento.strftime("%Y-%m-%d")
            resource['nivel'] = nivel
            resource['owner_org'] = organizacion['title']
            
            #log.info("[SelloExcelenciaView]  marcar_recurso_sello resource: %s", resource)

            # Mantener datastore_active si existe
            if 'datastore_active' in resource:
                resource['datastore_active'] = resource['datastore_active']

            # Actualizar
            update_resource = toolkit.get_action('resource_update')
            update_resource({'ignore_auth': True}, resource)

            


            #log.info("[SelloExcelenciaView]  marcar_recurso_sello marca guardada con exito")

            return True
        except Exception as e:
            log.error("[SelloExcelenciaView]  Error al guardar el archivo: $s",e)           
            return  False        
            
    def can_view(self, data_dict):
        return data_dict

    def setup_template_variables(self, context, data_dict):
        pass
        
    def view_template(self, context, data_dict):
        return 'sello_excelencia_view.html'

    def _get_sello_pdf(self, dataset_id):
        pass

    def listar_organizaciones(self):
        log.info("[SelloExcelenciaView]  listar_organizaciones Ejecutado")
        # El context suele incluir al usuario (puede ser sysadmin)
        context = {
            'model': model,
            'session': model.Session,
            'user': toolkit.c.user  # o el nombre de un usuario válido
        }


        data_dict = {
            'all_fields': True,   # Si quieres que traiga más datos
            'include_extras': True
        }

        orgs = toolkit.get_action('organization_list')(context, data_dict)

        '''for org in orgs:
            print(org['name'], "-", org.get('title'))'''

        return orgs  
        

  
