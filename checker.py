import re

class Checker:

    def __init__(self, firewall, display, verbose=False):
        self.firewall = firewall
        self.display = display
        self.verbose = verbose
        self.messages = []  # Lista para mensajes de log detallados (lo que antes era 'self.message')
        self.current_summary_message = None # Nuevo: para el mensaje principal/resumen
        self.log_messages = []  # Almacena mensajes con sus niveles (dict: {"message": msg, "level": lvl})
        self.result = "N/A"
        self.manual_entry = False
        self.auto = True
        self.enabled = True
        self.levels = None
        self.benchmark_author = None
        self.question_context = None
        self.question = None
        self.answer = None

    def __lt__(self, other):
        return self.id < other.id

    def is_valid(self):
        if self.id is None:
            print(f'[!] Error en {self.__class__.__name__}: ID de verificación no definido')
            return False
        if self.title is None:
            print(f'[!] Error en {self.__class__.__name__}: Título de verificación no definido')
            return False
        if self.levels is None or len(self.levels) == 0:
            print(f'[!] Error en {self.__class__.__name__}: Niveles no definidos')
            return False
        if self.benchmark_author is None or len(self.benchmark_author) == 0:
            print(f'[!] Error en {self.__class__.__name__}: Autor del benchmark no definido')
            return False
        return True

    def is_level_applicable(self, levels):
        for level in levels:
            if int(level) in self.levels:
                return True
        return False

    def print_verbose(self, content):
        self.display.log(f'\t| {content}', log_level="DEBUG")

    def restore_from_cache(self, cached_result):
        self.result = cached_result["result"]
        self.messages = cached_result.get("messages", []) # Restaurar la lista de mensajes detallados
        if not isinstance(self.messages, list):
            self.messages = [self.messages] 
        
        self.current_summary_message = cached_result.get("current_summary_message", None) # Restaurar el mensaje principal

        self.log_messages = cached_result.get("log_messages", [])
        if not isinstance(self.log_messages, list):
            if self.messages:
                self.log_messages = [{"message": self.messages[0], "level": self.result if self.result != "N/A" else "INFO"}]
            else:
                self.log_messages = []
        
        self.question = cached_result["question"]
        self.question_context = cached_result["question_context"]
        self.answer = cached_result["answer"]
        print(f'[{self.get_id()}] {self.title}', end='')
        print(f' : {self.result}')
        if self.verbose and self.question_context is not None:
            self.display.show(self.question_context)
        if self.verbose and self.question is not None:
            self.display.show(self.question)
        if self.verbose and self.answer is not None:
            self.display.show(self.answer)
        if self.verbose and self.messages:
            for msg_line in self.messages:
                self.display.show(msg_line)

    def skip(self):
        print(f'[{self.get_id()}] {self.title} : SKIP')
        self.result = 'SKIP'
        self.add_message("Verificación omitida.", log_level="SKIP")
        self.set_message("Verificación omitida por el usuario.") # Usar set_message aquí para el resumen final

    def run(self):
        if not self.is_valid():
            return False

        self.display.log(f"[{self.get_id()}] {self.title}", log_level="INFO")

        try:
            self.success = self.do_check()
            
            if self.success is None:
                self.result = 'SKIP'
            elif self.success:
                self.result = 'PASS'
            else:
                self.result = 'FAIL'

        except Exception as e:
            self.add_message(f"ERROR: Ocurrió un error inesperado durante la ejecución: {e}", log_level="ERROR")
            self.success = False
            self.result = "ERROR"
            self.set_message(f"ERROR inesperado: {e}") # Usar set_message para el resumen de error
            
        if not self.manual_entry:
            # Aquí mostramos el mensaje principal/resumen establecido por set_message
            print(f'[{self.get_id()}] {self.title} : {self.result}')
            if self.current_summary_message:
                self.display.show(f'  Mensaje: {self.current_summary_message}')

    def set_question_context(self, question_context):
        if not isinstance(question_context, list):
            self.question_context = [question_context]
        else:
            self.question_context = question_context

    def add_question_context(self, question_context):
        if self.question_context is None:
            self.question_context = []
        if isinstance(question_context, list):
            self.question_context.extend(question_context)
        else:
            self.question_context.append(question_context)

    def ask(self, question):
        self.manual_entry = True
        self.question = question
        self.answer = self.display.ask(self.question_context, question)
        return self.answer

    def ask_if_correct(self, question="¿Es correcto?"):
        answer = self.ask(question + " ([Y]es/[n]o/[s]kip)")
        
        if answer.lower() == 'n':
            self.add_message("Establecido manualmente como no conforme", log_level="FAIL")
            self.set_message("No conforme (manual).") # Usar set_message
            return False
        if answer.lower() == 's':
            self.add_message("Omitido", log_level="SKIP")
            self.set_message("Omitido (manual).") # Usar set_message
            return None
        else:
            self.add_message("Establecido manualmente como conforme", log_level="PASS")
            self.set_message("Conforme (manual).") # Usar set_message
            return True

    # --- Manejo de mensajes y logs ---
    def add_message(self, message, log_level="INFO"): 
        """
        Añade un mensaje a la lista de logs detallados de la verificación.
        Estos mensajes son para el registro completo de la ejecución.
        """
        if self.messages is None: # Esto ya no debería ser necesario si se inicializa como []
            self.messages = []
        
        if isinstance(message, list):
            self.messages.extend(message)
            for msg_item in message:
                self.log_messages.append({"message": msg_item, "level": log_level})
        else:
            self.messages.append(message)
            self.log_messages.append({"message": message, "level": log_level})

        if self.display:
            if self.verbose or log_level in ["PASS", "FAIL", "WARN", "ERROR", "SKIP"]:
                self.display.log(f"[{self.id}] {message}", log_level=log_level)

    def set_message(self, message):
        """
        Establece el mensaje principal/resumen de la verificación.
        Este mensaje sobrescribe cualquier mensaje anterior establecido por set_message.
        """
        self.current_summary_message = message
        # Decide si también quieres que este mensaje resumen se añada a la lista de logs detallados:
        # self.add_message(message, log_level="INFO") # Podrías añadirlo como INFO o PASS/FAIL según el contexto

    # --- Ayudantes internos ---
    def get_id(self):
        return f'{self.benchmark_author}-{self.id}'

    def get_result(self):
        return self.result
    
    def get_title(self):
        return self.title
    
    def get_log(self):
        """
        Retorna los mensajes de log acumulados para este verificador,
        formateados con niveles, incluyendo el mensaje resumen si existe.
        """
        formatted_logs = []
        if self.question_context:
            formatted_logs.append("CONTEXTO:")
            if isinstance(self.question_context, list):
                formatted_logs.extend([f"  - {ctx}" for ctx in self.question_context])
            else:
                formatted_logs.append(f"  - {self.question_context}")
        
        if self.question:
            formatted_logs.append(f"PREGUNTA: {self.question}")
        
        if self.answer:
            formatted_logs.append(f"RESPUESTA: {self.answer}")
        
        if self.current_summary_message: # Incluir el mensaje principal en el log
            formatted_logs.append(f"MENSAJE RESUMEN: {self.current_summary_message}")

        if self.log_messages:
            formatted_logs.append("LOG DETALLADO:")
            for entry in self.log_messages:
                formatted_logs.append(f"  {entry['level']}: {entry['message']}")
        
        # Si no hay log_messages y sí hay messages (por si hay inconsistencias previas)
        elif not self.log_messages and self.messages:
            formatted_logs.append("MENSAJES ANTIGUOS (Convertidos a INFO):")
            formatted_logs.extend([f"  INFO: {msg}" for msg in self.messages])

        return "\n".join(formatted_logs)

    def get_config(self, chapter=None):
        # Esta es una función de EJEMPLO. ¡Reemplázala con tu lógica real!
        if chapter == "system global":
            return {
                "hostname": "FortiGate-FW01",
                "admin-lockout-threshold": "3",
                "admin-lockout-duration": "60"
            }
        return None

    def is_ip(self, param):
        return re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$",param) is not None

    def is_fqdn(self, param):
        return re.match(r"^(?!:\/\/)(?=.{1,255}$)((.{1,63}\.){1,127}(?![0-9]*$)[a-z0-9-]+\.?)$",param) is not None

    def get_wan_interfaces(self):
        return self.firewall.get_wan_interfaces()