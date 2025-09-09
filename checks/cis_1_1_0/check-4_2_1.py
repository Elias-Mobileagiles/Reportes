from checker import Checker # Asegúrate de que esta importación apunte correctamente a tu clase Checker

class Check_CIS_4_2_1(Checker):

    def __init__(self, firewall, display, verbose=False):
        super().__init__(firewall, display, verbose)

        self.id = "4.2.1"
        self.title = "Antivirus Definition Push Updates are Configured"
        self.levels = [2]
        self.auto = True
        self.benchmark_version = "v1.1.0"
        self.benchmark_author = "CIS"

    def do_check(self):
        # Esta parte asume que self.get_config, self.set_message, y self.add_message
        # ahora se heredan correctamente de la clase Checker.

        config_autoupdate_pushupdate = self.get_config("system autoupdate push-update")

        if config_autoupdate_pushupdate is None:
            # Usamos add_message para un registro detallado
            self.add_message(f'No se encontró el bloque "autoupdate push-update" en la configuración o falló la recuperación.', log_level="INFO")
            # Usamos set_message para el mensaje resumen que se mostrará
            self.set_message(f'Falla: El bloque de actualización por "push" de antivirus no está configurado o no se pudo recuperar.')
            return False

        # Añadimos una verificación aquí para asegurar que config_autoupdate_pushupdate sea un diccionario
        if not isinstance(config_autoupdate_pushupdate, dict):
            self.add_message(f'La configuración recuperada para "autoupdate push-update" no tiene el formato de diccionario esperado. Se obtuvo: {type(config_autoupdate_pushupdate)}', log_level="ERROR")
            self.set_message(f'Falla: Formato de configuración inesperado para las actualizaciones por "push" de antivirus.')
            return False

        if "status" not in config_autoupdate_pushupdate.keys():
            self.add_message(f'No se encontró la clave "status" en la configuración de "autoupdate push-update".', log_level="INFO")
            self.set_message(f'Falla: La configuración de actualizaciones por "push" de antivirus no tiene la clave "status".')
            return False

        if not config_autoupdate_pushupdate["status"] == "enable":
            self.add_message("Las actualizaciones por \"push\" no están habilitadas.", log_level="INFO")
            # Si no están habilitadas, la verificación falla y establecemos el mensaje resumen
            self.set_message(f'Falla: Las actualizaciones por "push" de definiciones de antivirus NO están habilitadas. Estado actual: {config_autoupdate_pushupdate["status"]}.')
            return False
        else:
            self.add_message("Las actualizaciones por \"push\" están habilitadas.", log_level="INFO")
            # Si están habilitadas, la verificación pasa y establecemos el mensaje resumen
            self.set_message("Éxito: Las actualizaciones por \"push\" de definiciones de antivirus están configuradas y habilitadas.")
            return True