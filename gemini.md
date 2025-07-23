El proyecto va encaminado a el uso de un sitio web en el cual las personas puedan buscar trabajo y postularse en el mismo sitio.
Debe de ser muy practico, amigable y muy funcional desde las respuestas y peticiones que existan de por medio por parte de las personas registradas en el sistema e incluso desde que la visiten desde la WEB.
Las clases, metodos, variables deben de estar en español y usando buenas practicas de programación.
En el frontend debe de estar implementado el uso de WebResponsive.
Cada template de HTML debe de separarse en su .css y .js den cual tendran su mismo nombre y que sea más manejable.


   # Instrucciones del Proyecto para Gemini
    
    Este es un proyecto de bolsa de trabajo desarrollado con Django.
    
    ## Configuración y Ejecución
    
    1.  **Activar el entorno virtual:** Antes de ejecutar cualquier comando, activa el entorno virtual.
        ```bash
        source venv/bin/activate
        ```
    
    2.  **Instalar dependencias:** Si hay nuevas dependencias, instálalas desde `requirements.txt`.
        ```bash
        pip install -r requirements.txt
    
    
    3.  **Ejecutar el servidor de desarrollo:** Para iniciar la aplicación localmente.
      python manage.py runserver
    
    ## Pruebas (Testing)
    
   4. Para ejecutar el conjunto de pruebas, utiliza el siguiente comando:
  python manage.py test usuarios

    
    ## Base de Datos
    
    Las migraciones son una parte crucial de este proyecto.
    
    *   **Crear migraciones:** Cuando se realicen cambios en los modelos (`models.py`).
      python manage.py makemigrations
   1 *   **Aplicar migraciones:** Para actualizar el esquema de la base de datos.
      python manage.py migrate

    
   2 ## Estructura y Convenciones
   
   *   **`usuarios`**: Es la app principal. Contiene la lógica de negocio para perfiles, vacantes, postulaciones y CVs.
   *   **`config`**: Contiene la configuración principal del proyecto Django (`settings.py`, `urls.py`).
   *   **`templates`**: Contiene todas las plantillas HTML. Sigue la estructura de Django.
   *   **`static`**: Contiene los archivos estáticos (CSS, JavaScript, imágenes).
   *   **Estilo de código**: Sigue las convenciones de PEP 8 para Python y las mejores prácticas de Django. El código nuevo debe ser consistente con el código existente.
   *   **Idioma**: El código, los comentarios y la documentación están principalmente en español.