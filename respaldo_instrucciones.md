# Objetivo:

Crear una nueva VM con mejores capacidades y una mejor distribución en sus directorios, debido a que el actual no es posible hacer resize a la partición /var y /tmp

###### **Credenciales de VM:**

IP: 10.10.90.112
usuario: prodbt
contraseña:##""1qaz

###### **Conexión vía ssh:**

ssh prodbt@10.10.90.112 -p 22

**Descripción**

El proyecto esta en Django y en producción. Es una plataforma de Bolsa de Trabajo.

###### **Ruta del proyecto:**

/home/BT

##### **Configuraciones para Producción:**

###### Nginx:

cat /etc/nginx/sites-enabled/BT

server { listen 80; server_name bolsadetrabajo.movimex.gob.mx; location /static/ {
alias /var/www/bolsa-trabajo/staticfiles/;
}
location /media/ { alias /var/www/bolsa-trabajo/media/; autoindex off; access_log
off; expires 1y; add_header Cache-Control "public";
}
location / { include proxy_params; proxy_pass
http://unix:/home/BT/gunicorn_bt.sock; # Solo una vez cada cabecera
proxy_set_header Host $host; proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; # Este debe pasar el encabezado enviado por Apache
proxy_set_header X-Forwarded-Proto $http_x_forwarded_proto;
}
}

cat /etc/nginx/sites-available/BT
server { listen 80; server_name bolsadetrabajo.movimex.gob.mx; location /static/ {
alias /var/www/bolsa-trabajo/staticfiles/;
}
location /media/ { alias /var/www/bolsa-trabajo/media/; autoindex off; access_log
off; expires 1y; add_header Cache-Control "public";
}
location / { include proxy_params; proxy_pass
http://unix:/home/BT/gunicorn_bt.sock; # Solo una vez cada cabecera
proxy_set_header Host $host; proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; # Este debe pasar el encabezado enviado por Apache
proxy_set_header X-Forwarded-Proto $http_x_forwarded_proto;
}
}

###### Gunicorn:

sudo nano /etc/systemd/system/gunicorn_bt.service

GNU nano 7.2 /etc/systemd/system/gunicorn_bt.service
[Unit]
Description= Gunicorn daemon for Bolsa de Trabajo
After=network.target

[Service]
User=prodbt
Group=www-data
#RuntimeDirectory=gunicorn
EnvironmentFile=/home/BT/.env.production
WorkingDirectory=/home/BT
ExecStart=/home/BT/venv/bin/gunicorn --workers 8 --bind unix:/home/BT/gunicorn_bt.sock config.wsgi:application
[Install]
WantedBy=multi-user.target
