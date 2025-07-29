# usuarios/servicios/api_dipomex.py
import requests
import logging
from django.conf import settings
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

class ServicioDipomex:
    """
    Servicio para consultar información de códigos postales usando la API DIPOMEX.
    """
    
    def __init__(self):
        self.api_key = "c378e976bc21341d90b8dfdb28ffc93bc9082f1f"
        self.url_base = "https://api.tau.com.mx/dipomex/"
        self.timeout = 10  # Timeout en segundos
        
    def validar_codigo_postal(self, codigo_postal: str) -> bool:
        """
        Valida que el código postal tenga el formato correcto.
        
        Args:
            codigo_postal: Código postal a validar
            
        Returns:
            bool: True si es válido, False en caso contrario
        """
        if not codigo_postal:
            return False
            
        # Limpiar espacios y caracteres especiales
        codigo_limpio = codigo_postal.strip().replace(' ', '').replace('-', '')
        
        # Verificar que tenga exactamente 5 dígitos
        if len(codigo_limpio) != 5:
            return False
            
        # Verificar que sean todos números
        if not codigo_limpio.isdigit():
            return False
            
        return True
    
    def consultar_codigo_postal(self, codigo_postal: str) -> Dict:
        """
        Consulta la información de un código postal usando la API DIPOMEX.
        
        Args:
            codigo_postal: Código postal de 5 dígitos
            
        Returns:
            Dict con la respuesta de la API o información de error
        """
        try:
            # Validar formato del código postal
            if not self.validar_codigo_postal(codigo_postal):
                return {
                    'exito': False,
                    'error': 'El código postal debe tener exactamente 5 dígitos',
                    'codigo_error': 'FORMATO_INVALIDO'
                }
            
            # Limpiar código postal
            codigo_limpio = codigo_postal.strip().replace(' ', '').replace('-', '')
            
            # Configurar headers
            headers = {
                'APIKEY': self.api_key,
                'Content-Type': 'application/json',
                'User-Agent': 'BolsaTrabajo-EstadoMexico/1.0'
            }
            
            # Construir URL de consulta
            url_consulta = f"{self.url_base}v1/cp/{codigo_limpio}"
            
            logger.info(f"Consultando código postal: {codigo_limpio}")
            
            # Realizar petición a la API
            response = requests.get(
                url_consulta,
                headers=headers,
                timeout=self.timeout
            )
            
            # Verificar código de estado HTTP
            if response.status_code == 200:
                datos_api = response.json()
                return self._procesar_respuesta_exitosa(datos_api, codigo_limpio)
                
            elif response.status_code == 404:
                return {
                    'exito': False,
                    'error': f'El código postal {codigo_limpio} no fue encontrado',
                    'codigo_error': 'CP_NO_ENCONTRADO'
                }
                
            elif response.status_code == 401:
                logger.error("Error de autenticación con API DIPOMEX")
                return {
                    'exito': False,
                    'error': 'Error de autenticación con el servicio de códigos postales',
                    'codigo_error': 'AUTH_ERROR'
                }
                
            else:
                logger.error(f"Error HTTP {response.status_code}: {response.text}")
                return {
                    'exito': False,
                    'error': f'Error del servicio: {response.status_code}',
                    'codigo_error': 'API_ERROR'
                }
                
        except requests.exceptions.Timeout:
            logger.error("Timeout al consultar API DIPOMEX")
            return {
                'exito': False,
                'error': 'Tiempo de espera agotado al consultar el código postal',
                'codigo_error': 'TIMEOUT'
            }
            
        except requests.exceptions.ConnectionError:
            logger.error("Error de conexión con API DIPOMEX")
            return {
                'exito': False,
                'error': 'No se pudo conectar con el servicio de códigos postales',
                'codigo_error': 'CONNECTION_ERROR'
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en petición a API DIPOMEX: {str(e)}")
            return {
                'exito': False,
                'error': 'Error al consultar el código postal',
                'codigo_error': 'REQUEST_ERROR'
            }
            
        except Exception as e:
            logger.error(f"Error inesperado en consulta DIPOMEX: {str(e)}")
            return {
                'exito': False,
                'error': 'Error interno del servidor',
                'codigo_error': 'INTERNAL_ERROR'
            }
    
    def _procesar_respuesta_exitosa(self, datos_api: Dict, codigo_postal: str) -> Dict:
        """
        Procesa una respuesta exitosa de la API DIPOMEX.
        
        Args:
            datos_api: Respuesta JSON de la API
            codigo_postal: Código postal consultado
            
        Returns:
            Dict con los datos procesados
        """
        try:
            # Verificar estructura de la respuesta
            if not isinstance(datos_api, dict):
                return {
                    'exito': False,
                    'error': 'Respuesta inválida del servicio',
                    'codigo_error': 'INVALID_RESPONSE'
                }
            
            # Extraer información principal
            estado = datos_api.get('estado', '').strip()
            municipio = datos_api.get('municipio', '').strip()
            ciudad = datos_api.get('ciudad', '').strip()
            
            # Validar que tenemos la información mínima requerida
            if not estado or not municipio:
                return {
                    'exito': False,
                    'error': 'Información incompleta del código postal',
                    'codigo_error': 'DATOS_INCOMPLETOS'
                }
            
            # Obtener colonias si están disponibles
            colonias = []
            if 'colonias' in datos_api and isinstance(datos_api['colonias'], list):
                colonias = [
                    colonia.get('colonia', '').strip() 
                    for colonia in datos_api['colonias']
                    if colonia.get('colonia', '').strip()
                ]
            
            resultado = {
                'exito': True,
                'codigo_postal': codigo_postal,
                'estado': estado,
                'municipio': municipio,
                'ciudad': ciudad,
                'colonias': colonias,
                'total_colonias': len(colonias)
            }
            
            logger.info(f"Consulta exitosa para CP {codigo_postal}: {estado}, {municipio}")
            return resultado
            
        except Exception as e:
            logger.error(f"Error procesando respuesta DIPOMEX: {str(e)}")
            return {
                'exito': False,
                'error': 'Error al procesar la información del código postal',
                'codigo_error': 'PROCESSING_ERROR'
            }
    
    def es_estado_mexico(self, estado: str) -> bool:
        """
        Verifica si el estado corresponde al Estado de México.
        
        Args:
            estado: Nombre del estado
            
        Returns:
            bool: True si es Estado de México
        """
        if not estado:
            return False
            
        estado_normalizado = estado.lower().strip()
        
        # Posibles variaciones del nombre del Estado de México
        variaciones_edomex = [
            'estado de méxico',
            'méxico',
            'edo de méxico',
            'edo. de méxico',
            'estado de mexico',
            'mexico',
            'edomex'
        ]
        
        return estado_normalizado in variaciones_edomex
    
    def obtener_municipios_edomex(self) -> List[str]:
        """
        Obtiene una lista de municipios del Estado de México.
        
        Returns:
            List[str]: Lista de municipios
        """
        # Esta lista se puede obtener dinámicamente de la base de datos
        # Por ahora, retornamos los principales municipios
        return [
            'Toluca', 'Ecatepec de Morelos', 'Tlalnepantla de Baz', 'Nezahualcóyotl',
            'Naucalpan de Juárez', 'Chimalhuacán', 'Atizapán de Zaragoza', 'Cuautitlán Izcalli',
            'Tultitlán', 'Coacalco de Berriozábal', 'Texcoco', 'Ixtapaluca', 'Huixquilucan',
            'Metepec', 'La Paz', 'Chalco', 'Valle de Chalco Solidaridad', 'Nicolás Romero',
            'Tecámac', 'Lerma', 'Zumpango', 'Cuautitlán', 'Tultepec', 'Tepotzotlán',
            'Melchor Ocampo', 'Chicoloapan', 'Nextlalpan', 'Tezoyuca', 'Coyotepec'
        ]

# Función de utilidad para uso directo
def consultar_codigo_postal_dipomex(codigo_postal: str) -> Dict:
    """
    Función de utilidad para consultar un código postal usando DIPOMEX.
    
    Args:
        codigo_postal: Código postal a consultar
        
    Returns:
        Dict con el resultado de la consulta
    """
    servicio = ServicioDipomex()
    return servicio.consultar_codigo_postal(codigo_postal)