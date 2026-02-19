#Repositorio de Alojamiento


sudo mkdir -p ~/ckan/lib//default/
sudo chmod 777 ~/ckan/lib/default/

sudo chown `whoami` ~/ckan/lib/default/

cd ~/ckan/lib/default/

 #se descarga la aplicacion desde el git
 https://github.com/jumargo73/Ckan_Docker.git


 #se Despliega la Aplicacion 

 docker compose build
 docker compose up -d

 #comandos importantes
 docker compose down  Baja la Aplicacion sin eliminar Volumenes Asociados
 docker compose down -v  Adicional elimina los Volumenes   
 docker restart <contenedor> si se desea reiniciar solo un contenedor

 #configuraciones Adicionales
 #migraciones de Ckan 

Se abre el contenedor de la aplicacion

docker exec -u root -it  ckan-hijo-ckan-1 bash

ckan db upgrade ejecuta las migraciones de ckan creacion de las tablas basicas
python  csvgeojson_migrated.py crea tablas necesarias para que funcione las nuevas modalidades

/*Generar Token
ckan -c /srv/app/ckan.ini user token add datosabiertos datapusher

/*Generar Token

con quit se sale del contenedor

#configuracion de permisos datapusher

- docker exec -it ckan_docker-ckan-1 ckan -c /srv/app/ckan.ini datastore set-permissions > ds.sql

- docker cp ds.sql ckan_docker-db-1:/ds.sql

- docker exec -it ckan_docker-db-1 psql -U ckan_default -d datastore_default -f /ds.sql



Validar que todo quedo ok
docker exec -it ckan-hijo-db-1 bash  psql -U postgres
comandos
\l despliega las BD creadas
\dt Despliega las Tablas creadas


Validar Logs de los Contenedores  
docker logs -f  <contenedor>

Archivos importantes

.env variables de entorno
.docker-compose.yml archivo donde se configura los contenedores de la aplicacion
dockerfile archivo de configuracion del contenedor.


/*Crear Usuario Admin de la Aplicacion*/

federacion_api  
Permisos Admin
ckan -c /srv/app/ckan.ini sysadmin add federacion_api

Token
ckan -c /srv/app/ckan.ini user token add federacion_api federacion_api_token

curl -H "Authorization: mi-tokem" \
     https://mi-midominio/api/3/action/package_search \
     -d '{"rows": 1000}'

