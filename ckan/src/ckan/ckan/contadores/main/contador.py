import psycopg2
import uuid
from ckan.contadores.modelo.gestionDB import crearTableContador,existe_el_contador_dataset,insertarContadorBD,actualizarContadorBD,get_Consolidado_contador_grupo
from ckan.contadores.logica.conectarBD import connectar
from contadores.modelo.gestionDB import eliminarContador
import os,pprint

def actualizar_insertarRegistro(records,context):

    """
    Procedimiento que interactua con la vista para realizar la actualizacion del contador

   
    """ 
    
    conn=connectar()

    print("actualizar_insertarRegistro records:")
    pprint.pprint(records)

    print("actualizar_insertarRegistro context:")
    pprint.pprint(context)
    
    
    if(context.startswith('Crea')):

        print("actualizar_insertarRegistro is_Crea:")
        pprint.pprint(records)
      
        records=insertarContadorBD(records,conn,context)   
        
        print("actualizar_insertarRegistro is_Crea:")
        pprint.pprint(records)

    else:
         
        records=existe_el_contador_dataset(records,conn,context)

        print("actualizar_insertarRegistro No_is_Crea:")
        pprint.pprint(records)
       
        if (records['isCreate']==True):
            pass
        else:
            actualizarContadorBD(records,conn)                   
                
    

def getContador_viewDescargas(data):

    """
    Procedimiento que interactua con las vista para recibir info del contador en metodo post
   
    """ 
  
    conn=connectar()
    return get_Consolidado_contador_grupo(data,conn)    


def crear_TableContador():
    """
    Crea la tabla de contadores
   
    """ 
    conn=connectar()
    crearTableContador(conn)

def eliminaContador(id):
    """
    Elimina contador
   
    """ 
    conn=connectar()    
    eliminarContador(id,conn)
