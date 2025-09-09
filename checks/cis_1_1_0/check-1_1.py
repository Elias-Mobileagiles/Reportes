# Importa la clase base Checker desde el módulo checker
from checker import Checker

# Define la clase Check_CIS_1_1 que hereda de Checker
class Check_CIS_1_1(Checker):
    
    def __init__(self, firewall, display, verbose=False):
        """
        Constructor de la clase Check_CIS_1_1.

        Parámetros:
        - firewall: objeto o estructura que contiene la configuración del sistema.
        - display: bandera para mostrar resultados en pantalla.
        - verbose: modo detallado de salida (por defecto False).
        """
        super().__init__(firewall, display, verbose)

        # Metadatos del control CIS
        self.id = "1.1"  # Identificador del control
        self.title = "Ensure DNS server is configured"  # Título del control
        self.levels = [1]  # Nivel de criticidad (1 = básico)
        self.auto = True  # Indica que el chequeo es automatizable
        self.benchmark_version = "v1.1.0"  # Versión del benchmark
        self.benchmark_author = "CIS"  # Autor del benchmark

    def do_check(self):
        """
        Ejecuta la verificación del control CIS 1.1.

        Retorna:
        - True si la configuración DNS cumple con los requisitos.
        - False si falta alguna configuración o si las IPs no son válidas.
        """
        # Extrae el bloque de configuración DNS
        config_system_dns = self.get_config("system dns")

        # Verifica si el bloque DNS existe
        if config_system_dns is None:
            self.set_message('No "config system dns" bloc in configuration file')
            return False

        # Verifica existencia de DNS primario
        if "primary" not in config_system_dns.keys():
            self.set_message('No primary DNS configured')
            return False

        # Valida que el DNS primario sea una IP válida
        if not self.is_ip(config_system_dns["primary"]):
            self.set_message(f'{config_system_dns["primary"]} is not a valid IP for primary DNS')
            return False

        # Verifica existencia de DNS secundario
        if "secondary" not in config_system_dns.keys():
            self.set_message('No secondary DNS configured')
            return False

        # Valida que el DNS secundario sea una IP válida
        if not self.is_ip(config_system_dns["secondary"]):
            self.set_message(f'{config_system_dns["secondary"]} is not a valid IP for secondary DNS')
            return False

        # Agrega mensajes informativos si ambas IPs son válidas
        self.add_message(f'{config_system_dns["primary"]}')
        self.add_message(f'{config_system_dns["secondary"]}')

        # Retorna éxito en la verificación
        return True