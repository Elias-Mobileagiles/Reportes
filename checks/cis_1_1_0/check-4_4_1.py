from checker import Checker

class Check_CIS_4_4_1(Checker):

    def __init__(self, firewall, display, verbose=False):
        
        super().__init__(firewall, display, verbose)
        
        self.id = "4.4.1"
        self.title = "Block high risk categories on Application Control"
        self.levels = [1]
        self.auto = True
        self.benchmark_version = "v1.1.0"
        self.benchmark_author = "CIS"

    def do_check(self):
        appcontrol_profiles = self.firewall.get_appcontrol_profiles()
        
        fail = False

        if len(appcontrol_profiles) == 0:
            self.add_message('No Application Control profile')
            return False
        
        required_categories_blocked = ["P2P", "Proxy"]
        
        for appcontrol_profile in appcontrol_profiles:
            profile_name = appcontrol_profile.get("edit", "Perfil sin nombre") # Usa .get para evitar KeyError si 'edit' no existe
            self.add_message(f'Profile {profile_name}:')
            
            categories_blocked = []
            
            # --- INICIO DE LA CORRECCIÓN DE SEGURIDAD ---
            # 1. Verificar si 'configs' existe en el perfil
            if "configs" not in appcontrol_profile:
                self.add_message(f'AVISO: El perfil "{profile_name}" de Control de Aplicaciones no tiene la sección "configs" esperada. Se salta la verificación para este perfil.')
                fail = True # Consideramos esto como un fallo si la estructura no es la esperada para la auditoría
                continue # Pasa al siguiente perfil
            
            # 2. Verificar si 'configs' es una lista y si no está vacía
            if not isinstance(appcontrol_profile["configs"], list) or not appcontrol_profile["configs"]:
                self.add_message(f'AVISO: La sección "configs" del perfil "{profile_name}" no es una lista o está vacía. Se salta la verificación para este perfil.')
                fail = True # Consideramos esto como un fallo si la estructura no es la esperada para la auditoría
                continue # Pasa al siguiente perfil
            
            # 3. Verificar si el primer elemento en 'configs' (índice 0) tiene la clave 'edits'
            if "edits" not in appcontrol_profile["configs"][0]:
                self.add_message(f'AVISO: El primer elemento en "configs" del perfil "{profile_name}" no tiene la sección "edits" esperada. Se salta la verificación para este perfil.')
                fail = True # Consideramos esto como un fallo si la estructura no es la esperada para la auditoría
                continue # Pasa al siguiente perfil
            # --- FIN DE LA CORRECCIÓN DE SEGURIDAD ---

            for rule in appcontrol_profile["configs"][0]["edits"]:
                
                # Default action seems to be "Block"
                if "action" in rule.keys():
                    action = rule["action"]
                else:
                    action = "block"
                    
                # Show all applications
                if 'application' in rule.keys():
                    for app_id in rule['application']:
                        app_name = self.firewall.fortiguard.application_name_from_id(app_id)
                        if app_name is not None:
                            self.add_message(f'- Aplicación {app_name} definida en el perfil con acción {action}')
                        else:
                            self.add_message(f'- Aplicación desconocida con id {app_id} definida en el perfil con acción {action}')
                            
                # Show all categories
                if 'category' in rule.keys():
                    for category_id in rule['category']:
                        category_name = self.firewall.fortiguard.category_name_from_id(category_id)
                        if category_name is not None:
                            self.add_message(f'- Categoría {category_name} definida en el perfil con acción {action}')
                            if action == "block":
                                categories_blocked.append(category_id)
                        else:
                            self.add_message(f'- Categoría desconocida con id {category_id} definida en el perfil con acción {action}')
                            
            # Verify if categories that should be blocked are indeed blocked
            for category_to_block in required_categories_blocked:
                # Obtenemos el ID numérico de la categoría usando el nombre
                category_id_to_block = self.firewall.fortiguard.category_id_from_name(category_to_block)
                if category_id_to_block is None:
                    # Esto significa que el nombre de la categoría (P2P o Proxy) no se encontró en Fortiguard data
                    self.add_message(f'ERROR: No se pudo obtener el ID para la categoría "{category_to_block}". Verifica la base de datos Fortiguard.')
                    fail = True # Consideramos esto como un fallo ya que no podemos verificar completamente
                    continue # Pasa a la siguiente categoría a bloquear
                
                if category_id_to_block not in categories_blocked:
                    fail = True
                    self.add_message(f'- La Categoría {category_to_block} NO está bloqueada en el perfil {profile_name}')
                                
        if not fail:
            self.add_message('Todas las categorías de alto riesgo (P2P y Proxy) están bloqueadas en todos los perfiles de Control de Aplicaciones.')
            
        return not fail