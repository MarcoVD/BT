El proyecto va encaminado a el uso de un sitio web en el cual las personas puedan buscar trabajo y postularse en el mismo sitio.
Debe de ser muy practico, amigable y muy funcional desde las respuestas y peticiones que existan de por medio por parte de las personas registradas en el sistema e incluso desde que la visiten desde la WEB.
Las clases, metodos, variables deben de estar en español y usando buenas practicas de programación.

   1 # Instrucciones del Proyecto para Gemini
    2 
    3 Este es un proyecto de bolsa de trabajo desarrollado con Django.
    4 
    5 ## Configuración y Ejecución
    6 
    7 1.  **Activar el entorno virtual:** Antes de ejecutar cualquier comando, activa el entorno virtual.
    8     ```bash
    9     source venv/bin/activate
   10     ```
   11 
   12 2.  **Instalar dependencias:** Si hay nuevas dependencias, instálalas desde `requirements.txt`.
   13     ```bash
   14     pip install -r requirements.txt
   15 
   1 
   2 3.  **Ejecutar el servidor de desarrollo:** Para iniciar la aplicación localmente.
      python manage.py runserver
   1 
   2 ## Pruebas (Testing)
   3 
   4 Para ejecutar el conjunto de pruebas, utiliza el siguiente comando:
  python manage.py test usuarios

   1 
   2 ## Base de Datos
   3 
   4 Las migraciones son una parte crucial de este proyecto.
   5 
   6 *   **Crear migraciones:** Cuando se realicen cambios en los modelos (`models.py`).
      python manage.py makemigrations
   1 *   **Aplicar migraciones:** Para actualizar el esquema de la base de datos.
      python manage.py migrate

    1 
    2 ## Estructura y Convenciones
    3 
    4 *   **`usuarios`**: Es la app principal. Contiene la lógica de negocio para perfiles, vacantes, postulaciones y CVs.
    5 *   **`config`**: Contiene la configuración principal del proyecto Django (`settings.py`, `urls.py`).
    6 *   **`templates`**: Contiene todas las plantillas HTML. Sigue la estructura de Django.
    7 *   **`static`**: Contiene los archivos estáticos (CSS, JavaScript, imágenes).
    8 *   **Estilo de código**: Sigue las convenciones de PEP 8 para Python y las mejores prácticas de Django. El código nuevo debe ser consistente con el código existente.
    9 *   **Idioma**: El código, los comentarios y la documentación están principalmente en español.