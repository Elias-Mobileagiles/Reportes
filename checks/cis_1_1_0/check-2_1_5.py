from checker import Checker

class Check_CIS_2_1_5(Checker):

    def __init__(self, firewall, display, verbose=False):
        
        super().__init__(firewall, display, verbose)

        self.id = "2.1.5"
        self.title = "Ensure hostname is set"
        self.levels = [1]
        self.auto = True
        self.benchmark_version = "v1.1.0"
        self.benchmark_author = "CIS"

    def do_check(self):
        config_system_global = self.get_config("system global")

        if config_system_global is None:
            # Se cambió 'set_message' a 'add_message'
            self.add_message(f'No "config system global" bloc in configuration file')
            return False
        
        if "hostname" not in config_system_global.keys():
            # Se cambió 'set_message' a 'add_message'
            self.add_message("Hostname not configured")
            return False

        if config_system_global["hostname"].startswith("FortiGate"):
            # Se cambió 'set_message' a 'add_message'
            self.add_message(f'Hostname seems to be default value: {config_system_global["hostname"]}')
            return False

        # Se cambió 'set_message' a 'add_message'
        self.add_message(f'{config_system_global["hostname"]}')

        return True