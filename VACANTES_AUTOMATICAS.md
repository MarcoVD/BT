# Sistema de Cierre Automático de Vacantes

## Descripción
Este sistema permite cerrar automáticamente las vacantes que han llegado a su fecha límite (`fecha_limite`).

## Componentes implementados

### 1. Métodos en el modelo Vacante

#### `cerrar_por_vencimiento()`
Método de instancia que cierra una vacante individual si ha llegado a su fecha límite.

#### `cerrar_vacantes_vencidas()` 
Método de clase que cierra todas las vacantes vencidas en una sola operación.

### 2. Comando de management
**Archivo**: `usuarios/management/commands/cerrar_vacantes_vencidas.py`

**Uso**:
```bash
# Cerrar vacantes vencidas
python manage.py cerrar_vacantes_vencidas

# Modo simulación (dry-run) para ver qué vacantes se cerrarían
python manage.py cerrar_vacantes_vencidas --dry-run
```

## Configuración de ejecución automática

### Opción 1: Cron Job (Recomendado para servidores Linux)

Ejecutar el comando diariamente a las 00:05 AM:

```bash
# Editar crontab
crontab -e

# Agregar la siguiente línea:
5 0 * * * cd /home/marco/PycharmProjects/BT && /home/marco/PycharmProjects/BT/venv/bin/python manage.py cerrar_vacantes_vencidas >> /var/log/vacantes_automaticas.log 2>&1
```

### Opción 2: Systemd Timer (Linux moderno)

1. Crear archivo de servicio:
```bash
sudo nano /etc/systemd/system/cerrar-vacantes.service
```

Contenido:
```ini
[Unit]
Description=Cerrar vacantes vencidas
After=network.target

[Service]
Type=oneshot
User=www-data
WorkingDirectory=/home/marco/PycharmProjects/BT
Environment=PATH=/home/marco/PycharmProjects/BT/venv/bin
ExecStart=/home/marco/PycharmProjects/BT/venv/bin/python manage.py cerrar_vacantes_vencidas
```

2. Crear timer:
```bash
sudo nano /etc/systemd/system/cerrar-vacantes.timer
```

Contenido:
```ini
[Unit]
Description=Cerrar vacantes vencidas diariamente
Requires=cerrar-vacantes.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

3. Habilitar y iniciar:
```bash
sudo systemctl daemon-reload
sudo systemctl enable cerrar-vacantes.timer
sudo systemctl start cerrar-vacantes.timer
```

### Opción 3: Task Scheduler (Windows Server)

1. Abrir "Task Scheduler"
2. Crear tarea básica
3. Configurar para ejecutar diariamente
4. Acción: `python manage.py cerrar_vacantes_vencidas`
5. Directorio: `/home/marco/PycharmProjects/BT`

## Verificación y monitoreo

### Verificar funcionamiento manual:
```bash
# Probar en modo simulación
python manage.py cerrar_vacantes_vencidas --dry-run

# Ejecutar realmente
python manage.py cerrar_vacantes_vencidas
```

### Ver logs (con cron):
```bash
tail -f /var/log/vacantes_automaticas.log
```

### Ver logs (con systemd):
```bash
journalctl -u cerrar-vacantes.service
```

## Consideraciones importantes

1. **Zona horaria**: El sistema usa la zona horaria configurada en Django (`America/Mexico_City`)
2. **Estado de vacantes**: Solo cierra vacantes con estado 'publicada'
3. **Fecha límite**: Solo considera vacantes con `fecha_limite` definida y anterior a hoy
4. **Rendimiento**: Usa `bulk_update` para operaciones eficientes con múltiples vacantes

## Personalización

### Cambiar horario de ejecución:
- Modificar la expresión cron o el calendario de systemd
- Recomendado ejecutar en horarios de bajo tráfico (madrugada)

### Añadir notificaciones:
- Modificar el comando para enviar emails cuando se cierran vacantes
- Integrar con sistemas de logging centralizados

### Excluir vacantes específicas:
- Añadir filtros adicionales en el método `cerrar_vacantes_vencidas()`
- Por ejemplo, excluir vacantes destacadas o de categorías específicas