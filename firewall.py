import fortiguard

class Firewall:
    
    def __init__(self, config, display, verbose=False):
        self.config = config
        self.wan_interfaces = None # Se inicializa a None, será una lista de nombres de interfaces WAN (strings)
        self.display = display
        # Fortiguard object
        self.fortiguard = fortiguard.Fortiguard()
        self.all_timezones = {
            "01":"(GMT-11:00) Midway Island, Samoa",
            "02":"(GMT-10:00) Hawaii",
            "03":"(GMT-9:00) Alaska",
            "04":"(GMT-8:00) Pacific Time (US & Canada)",
            "05":"(GMT-7:00) Arizona",
            "81":"(GMT-7:00) Baja California Sur, Chihuahua",
            "06":"(GMT-7:00) Mountain Time (US & Canada)",
            "07":"(GMT-6:00) Central America",
            "08":"(GMT-6:00) Central Time (US & Canada)",
            "09":"(GMT-6:00) Mexico City",
            "10":"(GMT-6:00) Saskatchewan",
            "11":"(GMT-5:00) Bogota, Lima,Quito",
            "12":"(GMT-5:00) Eastern Time (US & Canada)",
            "13":"(GMT-5:00) Indiana (East)",
            "74":"(GMT-4:00) Caracas",
            "14":"(GMT-4:00) Atlantic Time (Canada)",
            "77":"(GMT-4:00) Georgetown",
            "15":"(GMT-4:00) La Paz",
            "87":"(GMT-4:00) Paraguay",
            "16":"(GMT-3:00) Santiago",
            "17":"(GMT-3:30) Newfoundland",
            "18":"(GMT-3:00) Brasilia",
            "19":"(GMT-3:00) Buenos Aires",
            "20":"(GMT-3:00) Nuuk (Greenland)",
            "75":"(GMT-3:00) Uruguay",
            "21":"(GMT-2:00) Mid-Atlantic",
            "22":"(GMT-1:00) Azores",
            "23":"(GMT-1:00) Cape Verde Is.",
            "24":"(GMT) Monrovia",
            "80":"(GMT) Greenwich Mean Time",
            "79":"(GMT) Casablanca",
            "25":"(GMT) Dublin, Edinburgh, Lisbon, London, Canary Is.",
            "26":"(GMT+1:00) Amsterdam, Berlin, Bern, Rome, Stockholm, Vienna",
            "27":"(GMT+1:00) Belgrade, Bratislava, Budapest, Ljubljana, Prague",
            "28":"(GMT+1:00) Brussels, Copenhagen, Madrid, Paris",
            "78":"(GMT+1:00) Namibia",
            "29":"(GMT+1:00) Sarajevo, Skopje, Warsaw, Zagreb",
            "30":"(GMT+1:00) West Central Africa",
            "31":"(GMT+2:00) Athens, Sofia, Vilnius",
            "32":"(GMT+2:00) Bucharest",
            "33":"(GMT+2:00) Cairo",
            "34":"(GMT+2:00) Harare, Pretoria",
            "35":"(GMT+2:00) Helsinki, Riga, Tallinn",
            "36":"(GMT+2:00) Jerusalem",
            "37":"(GMT+3:00) Baghdad",
            "38":"(GMT+3:00) Kuwait, Riyadh",
            "83":"(GMT+3:00) Moscow",
            "84":"(GMT+3:00) Minsk",
            "40":"(GMT+3:00) Nairobi",
            "85":"(GMT+3:00) Istanbul",
            "41":"(GMT+3:30) Tehran",
            "42":"(GMT+4:00) Abu Dhabi, Muscat",
            "43":"(GMT+4:00) Baku",
            "39":"(GMT+3:00) St. Petersburg, Volgograd",
            "44":"(GMT+4:30) Kabul",
            "46":"(GMT+5:00) Islamabad, Karachi, Tashkent",
            "47":"(GMT+5:30) Kolkata, Chennai, Mumbai, New Delhi",
            "51":"(GMT+5:30) Sri Jayawardenepara",
            "48":"(GMT+5:45) Kathmandu",
            "45":"(GMT+5:00) Ekaterinburg",
            "49":"(GMT+6:00) Almaty, Novosibirsk",
            "50":"(GMT+6:00) Astana, Dhaka",
            "52":"(GMT+6:30) Rangoon",
            "53":"(GMT+7:00) Bangkok, Hanoi, Jakarta",
            "54":"(GMT+7:00) Krasnoyarsk",
            "55":"(GMT+8:00) Beijing, ChongQing, HongKong, Urumgi, Irkutsk",
            "56":"(GMT+8:00) Ulaan Bataar",
            "57":"(GMT+8:00) Kuala Lumpur, Singapore",
            "58":"(GMT+8:00) Perth",
            "59":"(GMT+8:00) Taipei",
            "60":"(GMT+9:00) Osaka, Sapporo, Tokyo, Seoul",
            "62":"(GMT+9:30) Adelaide",
            "63":"(GMT+9:30) Darwin",
            "61":"(GMT+9:00) Yakutsk",
            "64":"(GMT+10:00) Brisbane",
            "65":"(GMT+10:00) Canberra, Melbourne, Sydney",
            "66":"(GMT+10:00) Guam, Port Moresby",
            "67":"(GMT+10:00) Hobart",
            "68":"(GMT+10:00) Vladivostok",
            "69":"(GMT+10:00) Magadan",
            "70":"(GMT+11:00) Solomon Is., New Caledonia",
            "71":"(GMT+12:00) Auckland, Wellington",
            "72":"(GMT+12:00) Fiji, Kamchatka, Marshall Is.",
            "00":"(GMT+12:00) Eniwetok, Kwajalein",
            "82":"(GMT+12:45) Chatham Islands",
            "73":"(GMT+13:00) Nuku'alofa",
            "86":"(GMT+13:00) Samoa",
            "76":"(GMT+14:00) Kiritimati"
        }
        
        # --- NUEVAS PROPIEDADES PARA CACHEAR DATOS PARSEADOS ---
        self._vips = None
        self._addresses = None # Para futuras referencias de objetos de dirección
        self._services = None
        self._service_groups = None
        # --- FIN NUEVAS PROPIEDADES ---

    def _get_edits_from_config(self, chapter):
        """
        Helper para obtener la lista de 'edits' de un capítulo de configuración.
        Retorna una lista vacía si el capítulo no existe o no tiene 'edits'.
        """
        config_block = self.get_config(chapter)
        if config_block and 'edits' in config_block:
            return config_block['edits']
        return []

    # Returns the config bloc in config dict
    def get_config(self, chapter=None):
        if chapter is None:
            return self.config
        else:
            for block in self.config:
                if "config" in block.keys() and block["config"] == chapter:
                    return block
            return None
    
    # Returns all firewall interfaces
    def get_interfaces(self):
        # Asumiendo que 'get_config("system interface")' ya devuelve el bloque con 'edits'
        return self._get_edits_from_config("system interface")
        
    # Returns all firewall zones
    def get_zones(self):
        return self._get_edits_from_config("system zone")
    
    # --- MODIFICACIONES EN get_wan_interfaces y set_wan_interfaces ---
    # get_wan_interfaces ahora devuelve SOLO los NOMBRES de las interfaces WAN
    def get_wan_interfaces(self):
        # Si self.wan_interfaces es una lista de strings (nombres), la devuelve directamente
        if isinstance(self.wan_interfaces, list):
            return self.wan_interfaces
        
        # Si aún no se han establecido, la lógica interactiva o de inventario
        # debería haberlas seteado a través de set_wan_interfaces.
        # Si llega aquí, significa que el script principal no las ha pasado
        # o se usó el modo "quiet". En este caso, el check de VIPs debería
        # considerar no poder determinar las WANs.
        if self.wan_interfaces is None:
            # Aquí, tu lógica existente para preguntar al usuario si 'self.wan_interfaces' es None
            # se ejecutaría. Pero, en el contexto de un checker automático,
            # no deberíamos preguntar. Es mejor devolver [] y que el checker maneje eso.
            # Sin embargo, si quieres que la pregunta se dispare siempre que no estén definidas,
            # puedes dejar la lógica interactiva. Para el check automático de VIPs,
            # es mejor que el Firewall no pregunte si no estamos en modo interactivo.
            # La asunción es que args.wan en el script principal ya pobló esto.

            # Para ser consistente con el comportamiento original de pedir al usuario
            # si no están seteadas, mantenemos la lógica de la pregunta si display está disponible
            # y no estamos en modo quiet (que manejaría el script principal).
            # Para el `ExposedVIPServicesCheck`, asumimos que las WANs *ya fueron* configuradas
            # por el script principal vía `set_wan_interfaces`.
            # Si quieres que el check funcione incluso si las WANs no se pasaron,
            # y quieres que el Firewall las deduzca o pregunte, esta lógica se mantiene.
            
            question_context = []
            question_context.append('All these interfaces exist on the device:')
            interfaces = self.get_interfaces()
            for interface in interfaces:
                name = interface["edit"]
                question_context.append(f'- {name}')
                
            question_context.append('All these zones exist on the device:')
            zones = self.get_zones()
            for zone in zones:
                name = zone["edit"]
                if isinstance(zone.get("interface"), list):
                    child_interfaces = ", ".join(zone["interface"])
                else:
                    child_interfaces = zone.get("interface", "N/A")
                question_context.append(f'- {name}: {child_interfaces}')
                
            # Asumiendo que `self.display.ask` no se usa si `--quiet` es True
            # Y que `set_wan_interfaces` ya fue llamado por el script principal
            # usando `args.wan`. Si no, esta parte interactiva se activaría.
            # Para el propósito del chequeo, si args.wan no se usa, o es silencioso,
            # y no se ha inicializado self.wan_interfaces, no tendremos interfaces WAN.
            # Por simplicidad, si la variable wan_interfaces no es una lista de strings,
            # asumimos que no se han configurado explícitamente y devolvemos una lista vacía.
            if self.display and not self.display.quiet: # Asegura que self.display existe y no estamos en modo quiet
                answer = self.display.ask(question_context, "Enter the WAN interfaces or zones, comma separated and case sensitive (for instance: port1,port2,zone_wan)")
                # La siguiente línea llama a set_wan_interfaces para poblar self.wan_interfaces
                self.set_wan_interfaces(answer.replace(" ", "").split(",")) 
            else:
                # Si no es interactivo o no hay interfaces seteadas, regresa una lista vacía
                # lo que significa que el check no encontrará WANs y reportará.
                return []
        
        # Si se llegó aquí, self.wan_interfaces ya debería ser una lista de strings.
        return self.wan_interfaces
    
    # Configures interfaces that should be considered WAN
    def set_wan_interfaces(self, interfaces_names_list):
        """
        Configura las interfaces que deben ser consideradas WAN.
        interfaces_names_list debe ser una lista de strings (nombres de interfaces/zonas).
        """
        # Almacenamos solo los nombres de las interfaces/zonas WAN.
        # El checker de VIPs solo necesita los nombres para comparar con srcintf/dstintf.
        self.wan_interfaces = interfaces_names_list 
    # --- FIN MODIFICACIONES EN get_wan_interfaces y set_wan_interfaces ---
    
    # Returns firewall policies. Allows filtering
    def get_policies(self, srcintfs=None, dstintfs=None, actions=None):
        config_firewall_policy = self.get_config("firewall policy")
        if config_firewall_policy is None:
            return []
        
        policies = config_firewall_policy['edits']

        result = []         
        for policy in policies:
            # Manejo de srcintf: Puede ser una cadena o una lista. Convertir a lista para consistencia.
            current_srcintf = policy.get("srcintf")
            if not isinstance(current_srcintf, list):
                current_srcintf = [current_srcintf] if current_srcintf is not None else []

            # Manejo de dstintf: Puede ser una cadena o una lista. Convertir a lista para consistencia.
            current_dstintf = policy.get("dstintf")
            if not isinstance(current_dstintf, list):
                current_dstintf = [current_dstintf] if current_dstintf is not None else []

            # Filtro por srcintfs (lista de NOMBRES de interfaces/zonas)
            if srcintfs is not None:
                # Verificamos si CUALQUIERA de las interfaces de origen de la política está en la lista de srcintfs
                if not any(s_intf in srcintfs for s_intf in current_srcintf):
                    continue
                
            # Filtro por dstintfs (lista de NOMBRES de interfaces/zonas)
            if dstintfs is not None:
                # Verificamos si CUALQUIERA de las interfaces de destino de la política está en la lista de dstintfs
                if not any(d_intf in dstintfs for d_intf in current_dstintf):
                    continue
                
            if actions is not None:
                if "action" not in policy.keys():
                    continue
                
                if policy["action"] not in actions:
                    continue
            
            result.append(policy)

        return result
    
    # --- NUEVO MÉTODO: get_vips ---
    def get_vips(self):
        """
        Retorna una lista de diccionarios de las configuraciones de VIPs.
        Cada diccionario representa una VIP y contiene sus propiedades.
        """
        if self._vips is None:
            self._vips = self._get_edits_from_config("firewall vip")
        return self._vips
    # --- FIN NUEVO MÉTODO: get_vips ---

    # --- NUEVO MÉTODO: resolve_service_to_ports ---
    def resolve_service_to_ports(self, service_name):
        """
        Resuelve un nombre de servicio FortiGate (predeterminado o custom)
        o un grupo de servicios a una lista de números de puerto (integers).
        """
        ports = set() # Usamos un set para evitar puertos duplicados

        # Cargar servicios y grupos de servicios si no están ya cargados
        if self._services is None:
            self._services = {s['edit']: s for s in self._get_edits_from_config("firewall service custom")}
        if self._service_groups is None:
            self._service_groups = {sg['edit']: sg for sg in self._get_edits_from_config("firewall service group")}

        if service_name.lower() == "all":
            # Si el servicio es "all", no podemos determinar puertos específicos.
            # Para este chequeo, si una política usa "all", se considera una exposición genérica
            # y no se buscarán puertos sensibles específicos en este método.
            # El check de VIPs está buscando puertos concretos.
            return [] 

        # 1. Buscar en los servicios personalizados (custom services)
        if service_name in self._services:
            svc_config = self._services[service_name]
            # FortiGate puede tener tcp-portrange, udp-portrange
            if 'tcp-portrange' in svc_config:
                self._add_ports_from_range(svc_config['tcp-portrange'], ports)
            if 'udp-portrange' in svc_config:
                self._add_ports_from_range(svc_config['udp-portrange'], ports)
            # Podrías añadir lógica para otros protocolos si fueran relevantes y tuviesen puertos

        # 2. Buscar en los grupos de servicios
        elif service_name in self._service_groups:
            group_config = self._service_groups[service_name]
            if 'member' in group_config:
                members = group_config['member']
                if isinstance(members, list):
                    for member_name in members:
                        # Recursivamente resolvemos los miembros del grupo
                        ports.update(self.resolve_service_to_ports(member_name))
                elif isinstance(members, str): # Si solo hay un miembro
                    ports.update(self.resolve_service_to_ports(members))
        
        # 3. Mapear servicios predefinidos de FortiGate a puertos conocidos
        # Esta es una lista parcial, puedes expandirla según necesites
        # Se verifica después de custom y grupos para darles prioridad
        elif service_name.upper() == "TELNET":
            ports.add(23)
        elif service_name.upper() == "SSH":
            ports.add(22)
        elif service_name.upper() == "HTTP":
            ports.add(80)
        elif service_name.upper() == "HTTPS":
            ports.add(443)
        elif service_name.upper() == "DNS":
            ports.add(53)
        elif service_name.upper() == "MS_RDP": # Nombre común para el servicio RDP predefinido
            ports.add(3389)
        elif service_name.upper() == "MS_SQL": # Nombre común para el servicio SQL predefinido
            ports.add(1433)
        elif service_name.upper() == "MYSQL": # A veces también está como servicio predefinido
            ports.add(3306)
        elif service_name.upper() == "POSTGRESQL": # A veces también está como servicio predefinido
            ports.add(5432)
        # Añade más servicios predefinidos según los nombres exactos que aparezcan en tu config
        # elif service_name.upper() == "FTP": ports.add(21)
        # elif service_name.upper() == "SMTP": ports.add(25)
        # etc.

        return sorted(list(ports)) # Retornar una lista ordenada de puertos

    def _add_ports_from_range(self, port_range_str, ports_set):
        """Helper para parsear rangos de puertos como '80' o '1000-2000' o '80 443'."""
        if not isinstance(port_range_str, str): 
            return

        parts = port_range_str.split() 
        for part in parts:
            if '-' in part:
                try:
                    start, end = map(int, part.split('-'))
                    for p in range(start, end + 1):
                        ports_set.add(p)
                except ValueError:
                    self.display.log(f"ADVERTENCIA: Rango de puerto inválido encontrado: '{part}'", log_level="WARN")
            else:
                try:
                    ports_set.add(int(part))
                except ValueError:
                    self.display.log(f"ADVERTENCIA: Puerto inválido encontrado: '{part}'", log_level="WARN")
                    pass

    # --- FIN NUEVO MÉTODO: resolve_service_to_ports ---

    # Returns ips sensors. Allows filtering
    def get_ips_sensors(self, names=None):
        return self._get_edits_from_config("ips sensor")
    
    # Return A/V profiles. Allows filtering
    def get_av_profiles(self, names=None):
        return self._get_edits_from_config("antivirus profile")
    
    # Returns DNS Filter profiles. Allows filtering
    def get_dnsfilter_profiles(self, names=None):
        return self._get_edits_from_config("dnsfilter profile")
    
    # Returns all service groups that includes a protocol (for instance "Windows AD" is returned when protocols = ["DNS"])
    def get_service_groups_containing_protocols(self, protocols=None):
        config_firewall_service_groups = self.get_config("firewall service group")
        if config_firewall_service_groups is None:
            return []
        
        service_groups = config_firewall_service_groups["edits"]
        
        result = []
        for service_group in service_groups:
            # Verificar si 'member' es una lista, puede ser una cadena si es un solo miembro
            members = service_group.get("member", [])
            if not isinstance(members, list):
                members = [members]

            if protocols is not None:
                for protocol in protocols:
                    if protocol in members: # Asume que 'protocols' son nombres de servicios
                        if service_group["edit"] not in result: # Evita duplicados en el resultado
                            result.append(service_group["edit"])
            else:
                # Si protocols es None, retorna todos los grupos de servicio (sus nombres 'edit')
                result.append(service_group["edit"]) # Solo el nombre del grupo
        return result

    # Returns App Control profiles. Allows filtering
    def get_appcontrol_profiles(self, names=None):
        return self._get_edits_from_config("application list")