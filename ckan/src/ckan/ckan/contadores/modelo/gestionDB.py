import json
from nis import cat
import uuid
import psycopg2
from tkinter import messagebox
from os import system 
#import urllib2
#import urllib
import requests
import ckan.lib.helpers as h
from datetime import datetime
import ckan.logic as logic

import requests
from ckan.contadores.logica.conectarBD import connectar,connectar_datastore
import ckan.lib.uploader as uploader
from decimal import Decimal
from paste.deploy import appconfig

#from ckan.logic.action.get import get_UrL

isCreate=False
def crearTableContador(conn):
    """
    Inserta la Tabla de contadores si no existe cuando se craa un nuevo grupo
    """
    try:
        
        cur=conn.cursor()
        sql="""
           DROP TABLE IF EXISTS public.contadores;

            CREATE TABLE public.contadores
                (
                    "id_Group" text COLLATE pg_catalog."default" NOT NULL,
                    "packageId" text COLLATE pg_catalog."default" NOT NULL,
                    "contVistas" bigint DEFAULT 0,
                    "contDownload" bigint DEFAULT 0,
                    "sourceId" text COLLATE pg_catalog."default" NOT NULL,
                    CONSTRAINT contadores_pkey PRIMARY KEY ("id_Group")
                )TABLESPACE pg_default;

            ALTER TABLE IF EXISTS public.contadores
            OWNER to ckan_default; 
			
			ALTER TABLE IF EXISTS public.contadores 
			ADD CONSTRAINT fk_package FOREIGN KEY("packageId") REFERENCES public.package("id");

			ALTER TABLE IF EXISTS public.contadores 
			ADD CONSTRAINT fk_resource FOREIGN KEY("sourceId") REFERENCES public.resource("id");	    
			
        """      
        cur.execute(sql)
        conn.commit()
        cur.close()
        conn.close()
    except (Exception, psycopg2.DatabaseError) as error:
        messagebox.showinfo(message=error, title="error")
        print(error)        
    finally:
        pass
        #if conn is not None:
        #    conn.close()  

def eliminarContador(id,conn):
    try:
        cur=conn.cursor()
        
        sql="""
        delete from public.contadores
        where "packageId"='{}'
        """.format(id)
        cur.execute(sql)
        conn.commit()
        cur.close()
        conn.close()
        #messagebox.showinfo(message=sql, title="del sql")

    except (Exception, psycopg2.DatabaseError) as error:
       
       messagebox.showinfo(message=error, title="error get_Consolidado_contador_grupo")
       print(error)        
    finally:
        pass
        #if conn is not None:
        #    conn.close()  
        

def get_Consolidado_contador_grupo(data,conn):
    try:
        """
        Funcion que retorna el registro de vistas y descargar que a tenido el conjunto de datos

        args:
        dict[]: recibe un diccionario con los datos del nombre del grupo y recurso a buscar


        Retorna la informacion del dict enviado añadiendo los datos pedidos en la consulta
        """
        cur=conn.cursor()
        sql="""
            SELECT SUM("contVistas"),SUM("contDownload")
            FROM public.contadores
            WHERE "sourceId"='{}'
            """.format(data["sourceId"])
        #messagebox.showinfo(message=sql, title="sql_get_Consolidado_contador_grupo") 
        cur.execute(sql)
        rows = cur.fetchall()
        conn.commit()
        cur.close()
        if (rows==None):
            data["contVistas"]='0'
            data["contDownload"]='0'
        else:
            for row in rows:
               
                    data["contVistas"]=int(row[0]) if row[0] is not None else 0     
               
                    data["contDownload"]=int(row[1]) if row[1] is not None else 0  
        # Imaginemos que obtienes esto como resultado de la consulta:
        resultado = (Decimal('15'), Decimal('6'))  # o (None, None) si no hay datos

        # Conversión segura:
        vistas = int(resultado[0]) if resultado[0] is not None else 0
        descargas = int(resultado[1]) if resultado[1] is not None else 0       

        print(f"get_Consolidado_contador_grupo' {data}'")        
        #messagebox.showinfo(message=data, title="data_ReturnDB")             
        return data    
    except (Exception, psycopg2.DatabaseError) as error:
        #messagebox.showinfo(message=error, title="error get_Consolidado_contador_grupo")
        print(error)        
    finally:
        pass
        #if conn is not None:
        #    conn.close()  
def get_consolidado_contador_group_dataset(data):
    pass

def get_contador_descargas(data,conn):

    """
        Funcion que retorna el registro de vistas y descargar que a tenido el conjunto de datos 
        la funcion de incrementar en uno segun el contexto

        args:
        dict[]: recibe un diccionario con los datos del nombre del grupo y recurso a buscar


        Retorna la informacion del dict enviado añadiendo los datos pedidos en la consulta
    """
    try:
        #messagebox.showinfo(message="get_contador_descargas", title="contadores") 
        existe=0
        cur=conn.cursor()
        sql="SELECT * FROM public.contadores where {}='{}' and {}='{}'".format('"packageId"',data['packageId'],'"sourceId"',data['sourceId'])
        #messagebox.showinfo(message=sql, title="get_contador_descargas") 
        cur.execute(sql)
        rows = cur.fetchall()
        conn.commit()
        cur.close()
        #conn.close()
        #messagebox.showinfo(message=rows[0], title="rows[0]")
        for row in rows:
            data["contadorId"]=row[0] 
            data["packageId"]=row[1]            
            data["contVistas"]=row[2]
            data["contDownload"]=row[3]
            data["sourceId"]=row[4]
        #messagebox.showinfo(message=data, title="data")
        return data
    except (Exception, psycopg2.DatabaseError) as error:
        messagebox.showinfo(message=error, title="error")
        print(error)        
    finally:
        pass
        #if conn is not None:
        #    conn.close()   
 

def existe_el_contador_dataset(data,conn,context):

    """
        Funcion que valida si existe el contador para el recurso , si no lo inserta en la tabla contadores 
        la funcion de incrementar en uno segun el contexto

        args:
        dict[]: recibe un diccionario con los datos del nombre del grupo y recurso a buscar


        Retorna la informacion del dict enviado añadiendo los datos pedidos en la consulta
    """

    try:
        registros={}
        isCreate=0
        #messagebox.showinfo(message=context, title="context existe_el_contador_dataset")
        cur=conn.cursor() 
        sql="SELECT count(*) registros FROM public.contadores where {}='{}' and {}='{}';".format('"packageId"',data['packageId'],'"sourceId"',data['sourceId'])
        #messagebox.showinfo(message=sql, title="existe_el_contador_dataset") 
        cur.execute(sql)
        rows = cur.fetchall()
        conn.commit()
        cur.close() 
        #conn.close()
        for row in rows:
            registros["registros"]=row[0]
        registro=registros["registros"]
        #messagebox.showinfo(message=registros, title="Registros regresados de la consulta")
        if (registro==0):
            insertarContadorBD(data,conn,context)
            data['isCreate']=True
            #messagebox.showinfo(message= isCreate, title= "isCreate")
            return data 
            
        else:
            data['isCreate']=False
            #messagebox.showinfo(message= isCreate, title= "isCreate")
            data=get_contador_descargas(data,conn)
            if  context.startswith('Down'):
                data["contDownload"]+=1
            elif (context.startswith('Visua')):
                data["contVistas"]+=1
            else:
                pass
        #messagebox.showinfo(message=data, title="data desde existe_el_contador_dataset registros!=0")
        return data                
    except (Exception, psycopg2.DatabaseError) as error:
        messagebox.showinfo(message=error, title="error_existe_el_contador_dataset")
        print(error)        
    finally:
        pass
        #if conn is not None:
        #    conn.close()        

def insertarContadorBD(records,conn,context):
    """
    Funcion que inserta el contador si no existe
    """
    try:
        id_Group = uuid.uuid4()
        cur=conn.cursor()
        data={}
        data["contadorId"]=id_Group 
        data["packageId"]=records['packageId']            
        data["sourceId"]=records['sourceId']
        data['isCreate']=True
        #messagebox.showinfo(message="else", title="No existe el grupo")
        if (context.startswith('Down')):
            sql="insert into public.contadores values ('{}','{}',{},{},'{}');".format(id_Group,records['packageId'],0,1,records['sourceId'])
            data["contVistas"]=0
            data["contDownload"]=1
        elif (context.startswith('Visua')):
            sql="insert into public.contadores values ('{}','{}',{},{},'{}');".format(id_Group,records['packageId'],1,0,records['sourceId'])
            data["contVistas"]=1
            data["contDownload"]=0
        else:
            sql="insert into public.contadores values ('{}','{}',{},{},'{}');".format(id_Group,records['packageId'],0,0,records['sourceId'])
            data["contVistas"]=0
            data["contDownload"]=0
        #messagebox.showinfo(message=sql, title="insertarContadorBD")
        cur.execute(sql)
        conn.commit()
        cur.close()
        return data
        #conn.close()
    except (Exception, psycopg2.DatabaseError) as error:
        messagebox.showinfo(message=error, title="error")
        print(error)        
    finally:
        pass
        #if conn is not None:
        #    conn.close()      
    

def actualizarContadorBD(records,conn):
    """
    Funcion que actualiza el contador si existe
    """
    try:

        records['isCreate']=False
        cur=conn.cursor()
        #messagebox.showinfo(message="else", title="No existe el grupo")
        sql="UPDATE public.contadores SET {}='{}', {}='{}' WHERE {}='{}' and {}='{}';".format('"contVistas"',records['contVistas'],'"contDownload"',records['contDownload'],'"packageId"',records['packageId'],'"sourceId"',records['sourceId'])              
        #messagebox.showinfo(message=sql, title="actualizarContadorBD")
        cur.execute(sql)
        conn.commit()
        cur.close()
        conn.close()
    except (Exception, psycopg2.DatabaseError) as error:
        messagebox.showinfo(message=error, title="error")
        print(error)        
    finally:
        pass
        #if conn is not None:
        #    conn.close()  


def test_config():
    licenses_file = config.get('ckan.licenses')
    site_url = config.get('ckan.site_url')
    print(f"Licenses file: {licenses_file}")
    print(f"Site URL: {site_url}")

def getPaquetesjsonBI():
    """Funcion que trae todos los dataset cargados en la BD"""
    try:
        tematicaName=""
        packageName=""       
        conn=connectar()
        cur=conn.cursor()


        
        url=config.get('ckan.site_url')

        '''list=logic.get_action('package_list')({}, {})
        
        print(f"getPaquetesjsonBI lista de packages Recibidos package_list {list}")'''
       
        
        data_contador={}             
        data={ "@context": "https://project-open-data.cio.gov/v1.1/schema/catalog.jsonld",
            "@type": "dcat:Catalog", 
            "conformsTo": "https://project-open-data.cio.gov/v1.1/schema", 
            "describedBy": "https://project-open-data.cio.gov/v1.1/schema/catalog.json", }

        data["dataset"]=[]

        sql="""
            SELECT 
            go.title,
            go.type,
            g.title,
            p.title,
            p.id,
            p.notes,
            p.type,
            p.license_id,
            p.metadata_created,
            p.metadata_modified,
            r.name,
            r.id,
            r.url,
            r.url_type,
            r.mimetype,
            p.id,
            p.frecuencia_actualizacion,
            p.departamento,
            p.ciudad
            FROM public.member m inner join public."package" p on m.table_id=p.id and m.capacity<>'organization'
            inner join public.resource r on r.package_id=p.id
            inner join public.group g on m.group_id=g.id 
            inner join public.group go on go.id=p.owner_org 
            where m.state='active' and g.state='active'
            and p.state='active' and r.state='active' 
            and m.table_name='package' 
        """
        #messagebox.showinfo(message=sql, title=" sql getPaquetesjson")
        cur.execute(sql)
        rows = cur.fetchall()
        conn.commit()               
        ciclo=0        
        for dataset in rows:
            ciclo+=1
            #messagebox.showinfo(message=ciclo, title=" sql dataset[3]")
            tematicaName=dataset[2]
            #messagebox.showinfo(message=dataset[2], title=" sql dataset[3]")
            #messagebox.showinfo(message=tematicaName, title=" sql tematicaName")      
            #messagebox.showinfo(message=dataset[3], title=" sql dataset[10]")
            #messagebox.showinfo(message=packageName, title=" sql packageName")      
            if((dataset[2]==tematicaName) and (dataset[3]==packageName)):
                    tematicaName=dataset[2]
                    packageName=dataset[3]
                    data_contador["sourceId"]=dataset[11]
                    dataResult=get_Consolidado_contador_grupo(data_contador,conn)
                    dataDict["Vistas"]=dataResult["contVistas"]
                    dataDict["Descargas"]=dataResult["contDownload"]
                    '''response = toolkit.get_action('datastore_search')(context, {'id': dataset[11]})
                    data = response.json()
                    columnas = list(data["result"]["fields"]) 
                    filas = list(data["result"]["fields"])
                    print(f"getPaquetesjsonBI Recibido desde Funcion datastore_search {columnas} {filas}")
                    #columnas, filas=getRow_Column(dataset[11]) 
                    '''
                    resourceDict={
                        "@type": "dcat:Distribution",
                        "Url":"{}".format(url+dataset[6]+'/'+dataset[4]+'/Resource/'+dataset[11]+'/download/'+dataset[12]),                        
                        "filas":filas,
                        "columnas":columnas,
                    }
                    #messagebox.showinfo(message=data, title=" sql data ciclo2") 
            elif((dataset[2]==tematicaName) and (dataset[3]!=packageName)):
                    
                    tematicaName=dataset[2]
                    packageName=dataset[3]

                    dataDict={}
                    dataDict["@type"]=""                                    
                    dataDict["Nombre"]=""
                    dataDict["Descripcion"]=""
                    dataDict["Dependencia"]=""
                    dataDict["Fecha_creacion"]=""                    
                    dataDict["Fecha_actualizacion"]=""
                    dataDict["Frecuencia_actualizacion"]=""
                    dataDict["Vistas"]=""
                    dataDict["Descargas"]=""  
                    dataDict["distribution"]=[]  
                    dataDict["@type"]="dcat:Dataset"                            
                    dataDict["Nombre"]=dataset[3]
                    dataDict["Descripcion"]=dataset[5]
                    dataDict["Dependencia"]=dataset[0]
                    dataDict["Fecha_creacion"]=dataset[8]
                    dataDict["Fecha_actualizacion"]=dataset[9]
                    dataDict["Frecuencia_actualizacion"]=dataset[16]
                    data_contador["sourceId"]=dataset[11]
                    dataResult=get_Consolidado_contador_grupo(data_contador,conn)
                    #response  = toolkit.get_action('datastore_search')({'user': context.get('user')}, {'id': pkg_id})
                    
                    print(f"getPaquetesjsonBI' {dataResult}'")
                    dataDict["Vistas"]=int(dataResult["contVistas"]) if dataResult["contVistas"] is not None else 0 
                    dataDict["Descargas"]=int(dataResult["contDownload"]) if dataResult["contDownload"] is not None else 0 
                    
                    '''response = toolkit.get_action('datastore_search')(context, {'id': dataset[11]})
                    data = response.json()
                    columnas = list(data["result"]["fields"]) 
                    filas = list(data["result"]["fields"])
                    #columnas, filas=getRow_Column(dataset[11]) 
                    print(f"getPaquetesjsonBI Recibido desde Funcion datastore_search {columnas} {filas}")
                    '''
                    resourceDict={
                        "@type": "dcat:Distribution",
                        "Url":"{}".format(url+dataset[6]+'/'+dataset[4]+'/Resource/'+dataset[11]+'/download/'+dataset[12]),                        
                        "filas":filas,
                        "columnas":columnas,
                    }
                    dataDict["distribution"].append(resourceDict)                    
                    #messagebox.showinfo(message=dataDict, title=" sql data ciclo1") 
                    data["dataset"].append(dataDict)
                    #messagebox.showinfo(message=data, title=" sql data ciclo1") 
            else:
                pass
        

        return data
        
        
    except (Exception, psycopg2.DatabaseError) as error:
        #messagebox.showinfo(message=error, title="error")
        print(error)        
    finally:
        pass
        #if conn is not None:
        #    conn.close()
        
def load_licenses(licenses_file):
        parser = configparser.ConfigParser()
        parser.read(licenses_file)
        licenses = {}
        for section in parser.sections():
            licenses[section] = dict(parser.items(section))

        print(f"load_licenses' {licenses}'")    
        return licenses

def get_license(licenses,license_id):
        print(f"get_license' {license_id}'")
        for key, val in licenses.items():
            if val.get('id') == license_id:
                print(f"get_license' {val}'")
                return val
        return None


def getPaquetesjson():
    """Funcion que trae todos los dataset cargados en la BD"""
    try:
        tematicaName=""
        packageName=""       
        conn=connectar()
        cur=conn.cursor()
        test_config()
        


        '''config = appconfig('config:/etc/ckan/default/produccion.ini')'''
       
        licenses_url = "http://licenses.opendefinition.org/licenses/groups/ckan.json"
        response = requests.get(licenses_url)
        licenses = response.json()

       
        url=config.get('ckan.site_url')  

      

        data={
            "@context": "https://project-open-data.cio.gov/v1.1/schema/catalog.jsonld",
            "@type": "dcat:Catalog", 
            "conformsTo": "https://project-open-data.cio.gov/v1.1/schema", 
            "describedBy": "https://project-open-data.cio.gov/v1.1/schema/catalog.json", 
           
                   }

        data["dataset"]=[]

        sql="""
            SELECT 
            go.title,
            go.type,
            g.title,
            p.name,
            p.id,
            p.notes,
            p.type,
            p.license_id,
            p.metadata_created,
            p.metadata_modified,
            r.name,
            r.id,
            r.url,
            r.url_type,
            r.mimetype,
            p.id,
            p.frecuencia_actualizacion,
            p.departamento,
            p.ciudad
            FROM public.member m inner join public."package" p on m.table_id=p.id and m.capacity<>'organization'
            inner join public.resource r on r.package_id=p.id
            inner join public.group g on m.group_id=g.id 
            inner join public.group go on go.id=p.owner_org 
            where m.state='active' and g.state='active'
            and p.state='active' and r.state='active' 
            and m.table_name='package' 
        """
        #messagebox.showinfo(message=sql, title=" sql getPaquetesjson")
        cur.execute(sql)
        rows = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()        
        ciclo=0  
              
        for dataset in rows:
            ciclo+=1
            #messagebox.showinfo(message=ciclo, title=" sql dataset[3]")
            tematicaName=dataset[2]
            #messagebox.showinfo(message=dataset[2], title=" sql dataset[3]")
            #messagebox.showinfo(message=tematicaName, title=" sql tematicaName")      
            #messagebox.showinfo(message=dataset[3], title=" sql dataset[10]")
            #messagebox.showinfo(message=packageName, title=" sql packageName")      
            if((dataset[2]==tematicaName) and (dataset[3]==packageName)):
                    tematicaName=dataset[2]
                    packageName=dataset[3]                    
                    resourceDict={
                        "@type": "dcat:Distribution",
					    "title": "CSV",
					    "format": "CSV",
					    "mediaType": "text/csv",
                        "accessURL":"{}".format(url+'/'+dataset[6]+'/'+dataset[4]+'/resource/'+dataset[11]+'/download/'+dataset[12]),
                        }
                    dataDict["distribution"].append(resourceDict)
                    #messagebox.showinfo(message=data, title=" sql data ciclo2") 
            elif((dataset[2]==tematicaName) and (dataset[3]!=packageName)):
                    
                    tematicaName=dataset[2]
                    packageName=dataset[3]

                    dataDict={}
                    dataDict["@type"]=""
                    dataDict["identifier"]=""
                    dataDict["landingPage"]={}
                    dataDict["title"]=""
                    dataDict["description"]=""
                    dataDict["keyword"]=[]
                    dataDict["issued"]=""
                    dataDict["modified"]=""
                    dataDict["publisher"]={}
                    dataDict["contactPoint"]={}
                    dataDict["accessLevel"]=""
                    dataDict["license"]=""
                    dataDict["distribution"]=[]
                    dataDict["theme"]=[]
                    dataDict["frecuencia"]=""
                    dataDict["departamento"]=""
                    dataDict["ciudad"]=""
                    
                    
                    dataDict["@type"]="dcat:Dataset"
                    dataDict["identifier"]="{}".format(dataset[4])
                    dataDict["landingPage"]="{}".format(url+'/'+dataset[6]+'/'+dataset[3])
                    dataDict["title"]=dataset[3]
                    dataDict["description"]=dataset[5]
                    dataDict["keyword"]=getTags(dataset[15])
                    dataDict["issued"]=dataset[8]
                    dataDict["modified"]=dataset[9]
                    dataDict["publisher"]={
                                "@type": "{}".format("org:"+dataset[1]),
                                "name": "Gobernacion Valle del Cauca"
                        }
                    dataDict["contactPoint"]={
                                "@type": "vcard:Contact", 
                                "hasEmail": "mailto:wgonzalez@sdp.gov.co", 
                                "fn": "{}".format(dataset[2])
                        }
                    dataDict["accessLevel"]="Public"
                     # Buscar la URL de una licencia seleccionada
                    selected_license_id = dataset[7]  # Por ejemplo, obtenida desde un dataset CKAN

                    license_url = next(
                        (lic["url"] for lic in licenses if lic["id"] == selected_license_id),
                        "https://example.com/license-not-found"
                    )
            
                    print("dataset[7]:", dataset[7])
                    print("URL de la licencia:", license_url)
                    
                    dataDict["license"]=license_url   
                    resourceDict={
                        "@type": "dcat:Distribution",
					    "title": "CSV",
					    "format": "CSV",
					    "mediaType": "text/csv",
                        "accessURL":"{}".format(url+'/'+dataset[6]+'/'+dataset[4]+'/resource/'+dataset[11]+'/download/'+dataset[12])
                        }
                    dataDict["distribution"].append(resourceDict)
                    dataDict["theme"].append(dataset[2])
                    dataDict["frecuencia"]=dataset[16]
                    dataDict["departamento"]=dataset[17]
                    dataDict["ciudad"]=dataset[18]
                    
                    
                    #messagebox.showinfo(message=dataDict, title=" sql data ciclo1") 
                    data["dataset"].append(dataDict)
                    #messagebox.showinfo(message=data, title=" sql data ciclo1") 
            else:
                pass
        #messagebox.showinfo(message=data, title="data") 

        #url_new="/usr/lib/ckan/default/src/ckan/ckan/public/base/json/data.json"
        #url_new="/home/ckan/ckan/lib/default/src/ckan/ckan/public/base/json/data.json"
        
       
        
        '''with open(url_new,"w") as file:
            #json.dump(data,file,indent=4, default=str)
            json.dump(data, file, ensure_ascii=False, indent=2,default=convertir_fechas)'''

        #archivo=open(url_new, "r") 
        #messagebox.showinfo(message=archivo, title="archivo") 
        #response_dict=json.load(archivo)  # will be { "firstname": "John", "lastname": "Doe", "age": 35 }
        return data #response_dict
        
    except (Exception, psycopg2.DatabaseError) as error:
        raise TypeError(f"Tipo no serializable: {type(error)}")
        print(error)        
    finally:
        pass
        #if conn is not None:
        #    conn.close()  

def convertir_fechas(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Tipo no serializable: {type(obj)}")

def getTags(id):
    """Funcion que trae todos los tags del dataset cargados en la BD"""
    try:
        conn=connectar()
        cur=conn.cursor()
        tags=[]
        sql="""
        select t.name
        from public.package_tag pt inner join public.tag t on t.id=pt.tag_id
        where package_id='{}'
        """.format(id)
        #messagebox.showinfo(message=sql, title="sql getTags")
        cur.execute(sql)
        rows = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        for row in rows:
            if row and isinstance(row[0], str) and row[0].strip():
                tags.append(row[0].strip())
        
        #messagebox.showinfo(message=tags, title="tags getTags")
        return tags

    except (Exception, psycopg2.DatabaseError) as error:
        messagebox.showinfo(message=error, title="error")
        print(error)        
    finally:
        pass
        #if conn is not None:
        #    conn.close()  


def getRow_Column(resource_id):
    try:
        print(f"getRow_Column")
        conn=connectar_datastore()
        cur=conn.cursor()
        # Validar si la tabla existe
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = %s
            );
        """, (resource_id,))

        exists = cur.fetchone()[0]

        if exists:
            
            sql='SELECT * FROM public."{}";'.format(resource_id)
            #messagebox.showinfo(message=sql, title="sql_getRow_Column")
            print(sql)
            cur.execute(sql)
            filas = cur.fetchall()
            conn.commit()        
            cur.close()
            conn.close() 

            if filas:
                num_filas=int(len(filas)) if len(filas) is not None else 0 
                #messagebox.showinfo(message=num_filas, title="num_filas")
                num_columnas=int(len(filas[0]) if len(filas[0])is not None else 0 )
                #messagebox.showinfo(message=num_columnas, title="num_columnas")
            else:
                num_filas=0  
                num_columnas=0

            if num_filas is None:
                num_filas=0

            if num_columnas is None:
                num_columnas=0    

            print(f"getRow_Column envio desde Funcion {num_columnas} {num_filas}")
     
            return num_columnas, num_filas
        else:
                print(f"La tabla '{resource_id}' no existe.")
                num_filas=0  
                num_columnas=0 
                return num_columnas, num_filas
                
    except (Exception, psycopg2.DatabaseError) as error:
        #messagebox.showinfo(message=error, title="error")
        print(error)        
    finally:
        pass
        #if conn is not None:
        #    conn.close()         
 

def getDataset():
    conn=connectar()
    cur=conn.cursor()
    sql="""
             SELECT DISTINCT
            p.title,
            p.name,
            p.id,
            p.notes,
            p.type,
            p.license_id,
            p.metadata_created,
            p.metadata_modified,
			co."sourceId"             
            FROM public.member m inner join public."package" p on m.table_id=p.id and m.capacity<>'organization'
            inner join public.resource r on r.package_id=p.id
            inner join public.group g on m.group_id=g.id 
            inner join public.group go on go.id=p.owner_org
            inner join public.contadores co on co."packageId"=p.id              
            where m.state='active' and g.state='active'
            and p.state='active' and r.state='active' 
            and m.table_name='package' 
            and p.private=false	
            order by p.metadata_modified desc limit 3
        """
    cur.execute(sql)
    rows = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    data={}
    data["package"]=[]
    con=0
    for dataset in rows:
        #messagebox.showinfo(message=dataset[8], title="resouce_id")
       
        #columnas,filas=getRow_Column(dataset[8])

        #messagebox.showinfo(message=filas, title="filas")
        #messagebox.showinfo(message=columnas, title="columnas")
        dataDict={}        
        dataDict["title"]=dataset[0]
        dataDict["name"]=dataset[1]
        dataDict["description"]=dataset[3]
        dataDict["type"]=dataset[4]
        dataDict["modified"]=str(dataset[7])
        dataDict["packageId"]=str(dataset[2])
        dataDict["sourceId"]=str(dataset[8])        
        data["package"].append(dataDict)
        con+=1
    data["packages"]=con
    return data    


