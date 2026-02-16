from tkinter import messagebox
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
    
    #messagebox.showinfo(message="actualizar_insertarRegistros_Contadores", title="clase contadores")
    #messagebox.showinfo(message=records, title="clase contadores records")
    if(context.startswith('Crea')):

        print("actualizar_insertarRegistro is_Crea:")
        pprint.pprint(records)
        #messagebox.showinfo(message=context, title="context")  
        records=insertarContadorBD(records,conn,context)   
        
        print("actualizar_insertarRegistro is_Crea:")
        pprint.pprint(records)

    else:
        #messagebox.showinfo(message=context, title="context")  
        records=existe_el_contador_dataset(records,conn,context)

        print("actualizar_insertarRegistro No_is_Crea:")
        pprint.pprint(records)
        #messagebox.showinfo(message=records['isCreate'], title="records['isCreate']")  
        if (records['isCreate']==True):
            pass
        else:
            actualizarContadorBD(records,conn)                   
                
    

def getContador_viewDescargas(data):

    """
    Procedimiento que interactua con las vista para recibir info del contador en metodo post
   
    """ 
    #messagebox.showinfo(message=data, title="data_getContador_viewDescargas")  
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
