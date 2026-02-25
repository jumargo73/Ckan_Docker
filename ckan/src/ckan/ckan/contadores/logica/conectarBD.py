import psycopg2


def getConeccion():
    try:
        conn = psycopg2.connect(database = "ckan_default", 
                            user = "ckan_default", 
                            host= 'db',
                            password = "car2986"#,
                            #port = 5432
                            )
       
        return conn
    except (Exception, psycopg2.DatabaseError) as error:
        
        print(error)
        return None
    finally:
        pass
        #if conn is not None:
         #conn.close()
         #print('Database connection closed.')

def getConeccion_datastore():
    try:
        conn = psycopg2.connect(database = "datastore_default", 
                            user = "datastore_default", 
                            host= 'db',
                            password = "car2986"#,
                            #port = 5432
                            )
       
        return conn
    except (Exception, psycopg2.DatabaseError) as error:
        
        print(error)
        return None
    finally:
        pass
        #if conn is not None:
        #conn.close()
        #print('Database connection closed.')


def connectar():
    conn = None   
    conn=getConeccion()
    return conn

def connectar_datastore():
    conn = None   
    conn=getConeccion_datastore()
    return conn