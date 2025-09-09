# checks/cis_1_1_0/check-1_4.py

from checker import Checker # Assuming 'checker.py' is in the root directory
import re # Needed for more robust port searching (though the current approach relies on direct matches)

class ExposedVIPServicesCheck(Checker):
    def __init__(self, firewall, display, verbose=False):
        super().__init__(firewall, display, verbose)
        
        self.id = "FG-VIP"
        self.title = "Identificación de VIPs expuestas"
        self.description = "Verifica si existen políticas de firewall que permitan acceso desde interfaces WAN a Virtual IPs (VIPs) en puertos comúnmente asociados a servicios sensibles como SQL Server (1433), RDP (3389), SSH (22), Telnet (23), MySQL (3306), PostgreSQL (5432)."
        self.enabled = True
        self.auto = True
        self.levels = [1, 2] # Levels at which this check should run
        
        self.benchmark_version = "1.0" 
        self.benchmark_author = "_"

        # Define the list of sensitive ports and their common descriptions
        self.sensitive_ports = {
            1433: "SQL Server",
            3389: "RDP",
            23: "Telnet",
            22: "SSH",
            3306: "MySQL",
            5432: "PostgreSQL"
        }

    def do_check(self):
        # Initialize flag to track if any exposed VIPs are found
        exposed_vips_found = False
        
        # Retrieve VIPs, policies, and WAN interface names from the Firewall object
        vips_list = self.firewall.get_vips() 
        policies = self.firewall.get_policies(actions=['accept']) 
        wan_interface_names = self.firewall.get_wan_interfaces() 

        # If no WAN interfaces are defined, we cannot check for internet exposure
        if not wan_interface_names:
            self.add_message("ADVERTENCIA: No se han definido interfaces WAN o no se pudieron determinar. No se puede verificar la exposición de VIPs a internet.", log_level="WARN")
            return True # Consider it a "PASS" for this check if no WANs are present to expose from

        # Dictionary to store unique exposures, preventing duplicate reports for the same policy/VIP
        reported_exposures = {}

        # Iterate through each firewall policy
        for policy in policies:
            policy_id = policy.get('policyid', policy.get('name', 'N/A')) # Get policy ID or name
            
            # Ensure srcintf is a list for consistent iteration
            policy_srcintf = policy.get("srcintf", [])
            if not isinstance(policy_srcintf, list):
                policy_srcintf = [policy_srcintf] if policy_srcintf is not None else []

            # Check if any source interface of the policy is a WAN interface
            from_wan = any(src_intf_name in wan_interface_names for src_intf_name in policy_srcintf)
            
            if from_wan:
                # Ensure dstaddr is a list for consistent iteration
                dst_addrs = policy.get('dstaddr', [])
                if not isinstance(dst_addrs, list):
                    dst_addrs = [dst_addrs] if dst_addrs is not None else []

                # Iterate through each destination address in the policy
                for dst_addr_name in dst_addrs:
                    # Search for the VIP configuration that matches the destination address name
                    target_vip_config = None
                    for vip_item in vips_list:
                        if vip_item.get('edit') == dst_addr_name:
                            target_vip_config = vip_item
                            break
                    
                    if target_vip_config: # If the destination is a VIP
                        vip_name = target_vip_config.get('edit')
                        # Extract the mapped IP address (can be a list or a single string)
                        mapped_ip_raw = target_vip_config.get('mappedip', 'N/A')
                        mapped_ip = mapped_ip_raw[0] if isinstance(mapped_ip_raw, list) and mapped_ip_raw else mapped_ip_raw
                        
                        # Get services defined in the policy
                        services_in_policy = policy.get('service', [])
                        if not isinstance(services_in_policy, list):
                            services_in_policy = [services_in_policy] if services_in_policy is not None else []

                        # Iterate through each service in the policy
                        for service_name in services_in_policy:
                            # Resolve the service name to a list of integer port numbers
                            resolved_ports = self.firewall.resolve_service_to_ports(service_name)
                            
                            # Filter for sensitive ports that are actually exposed by this service
                            exposed_critical_ports = [
                                port for port in resolved_ports if port in self.sensitive_ports
                            ]
                            
                            if exposed_critical_ports:
                                exposed_vips_found = True
                                
                                # Create a unique key to prevent redundant reporting of the same exposure
                                exposure_key = (policy_id, vip_name) # Using policy ID and VIP name as key
                                
                                if exposure_key not in reported_exposures:
                                    reported_exposures[exposure_key] = {
                                        "policy_id": policy_id,
                                        "vip_name": vip_name,
                                        "mapped_ip": mapped_ip,
                                        "services": []
                                    }
                                
                                # Add only the sensitive ports found for this specific service
                                for port in exposed_critical_ports:
                                    service_detail = {
                                        "service_name": service_name,
                                        "port": port,
                                        "description": self.sensitive_ports.get(port, "Unknown sensitive port")
                                    }
                                    # Avoid adding duplicate port entries for the same service if it's already there
                                    if service_detail not in reported_exposures[exposure_key]["services"]:
                                        reported_exposures[exposure_key]["services"].append(service_detail)

        # Generate the final message based on findings
        if exposed_vips_found:
            message_details = [
                "Se encontraron VIPs expuestas desde interfaces WAN a puertos sensibles (SQL, RDP, SSH, Telnet, MySQL, PostgreSQL):"
            ]
            for key, info in reported_exposures.items():
                ports_info = []
                # Sort services for consistent output
                sorted_services = sorted(info['services'], key=lambda x: x['port'])
                for svc_info in sorted_services:
                    ports_info.append(f"{svc_info['port']} ({svc_info['description']})")
                
                message_details.append(
                    f" - Política: {info['policy_id']}, "
                    f"VIP: {info['vip_name']} (Mapea a: {info['mapped_ip']}), "
                    f"Puertos expuestos: {', '.join(ports_info)}."
                )
            
            self.add_message("\n".join(message_details), log_level="FAIL") # Log as FAIL if exposures are found
            return False # The check fails
        else:
            self.add_message("No se encontraron VIPs expuestas desde interfaces WAN a puertos sensibles (SQL, RDP, SSH, Telnet, MySQL, PostgreSQL).", log_level="PASS")
            return True # The check passes
