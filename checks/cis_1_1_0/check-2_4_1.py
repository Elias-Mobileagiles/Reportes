from checker import Checker

class Check_CIS_2_4_1(Checker):

    def __init__(self, firewall, display, verbose=False):
        
        super().__init__(firewall, display, verbose)

        self.id = "2.4.1"
        self.title = "Ensure default 'admin' password is changed"
        self.levels = [1]
        self.auto = False # <--- Es un cheque manual, lo que explica 'ask_if_correct'
        self.enabled = True
        self.benchmark_version = "v1.1.0"
        self.benchmark_author = "CIS"


    def do_check(self):
        # --- INICIO DE LA CORRECCIÓN ---
        # Inicializamos la variable a False.
        # Esto asegura que siempre tendrá un valor, incluso si el bucle no la asigna.
        username_admin_exists = False
        # --- FIN DE LA CORRECCIÓN ---

        config_system_admin = self.get_config("system admin")

        if config_system_admin is None:
            self.set_message(f'No \"config system admin\" block defined')
            # Si no hay bloque 'system admin', no podemos verificar,
            # pero por la naturaleza de un benchmark CIS, esto debería ser un FALLO
            # a menos que tu lógica determine lo contrario para este caso específico.
            # Aquí lo mantendremos como lo tenías, devolviendo False.
            return False

        # Asumiendo que 'edits' es una lista de diccionarios, y cada diccionario tiene una clave 'edit'.
        if len(config_system_admin.get('edits', [])) > 0: # Usar .get para evitar KeyError si 'edits' no existe
            for edit_item in config_system_admin['edits']: # Cambié 'edit' a 'edit_item' para evitar confusión con edit["edit"]
                # Aseguramos que 'edit_item' es un diccionario y que contiene la clave 'edit'
                if isinstance(edit_item, dict) and "edit" in edit_item:
                    username = edit_item["edit"]
                    if username == "admin":
                        username_admin_exists = True
                        break # Salimos del bucle una vez que encontramos al usuario 'admin'

        if username_admin_exists:
            # Si el usuario 'admin' existe, se pregunta al usuario si la contraseña predeterminada fue cambiada.
            return self.ask_if_correct('"admin" user exists. Is the default password changed?')
        else:
            # Si el usuario 'admin' no existe, se considera que el requisito no aplica y se pasa.
            self.set_message('User "admin" does not exist so this requirement is not really applicable. Considering PASS')
            return True