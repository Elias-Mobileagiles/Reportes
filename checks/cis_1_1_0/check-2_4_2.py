from checker import Checker

class Check_CIS_2_4_2(Checker):

    def __init__(self, firewall, display, verbose=False):
        
        super().__init__(firewall, display, verbose)

        self.id = "2.4.2"
        self.title = "Ensure all the login accounts having specific trusted"
        self.levels = [1]
        self.auto = True
        self.enabled = True
        self.benchmark_version = "v1.1.0"
        self.benchmark_author = "CIS"


    def do_check(self):
        # get_config should return the entries for "system admin"
        # This will likely be a list of dictionaries, where each dictionary is an admin user.
        config_system_admin_entries = self.get_config("system admin")

        # Handle the case where no 'config system admin' block is found or it's empty
        if not config_system_admin_entries: # This covers None or empty list
            self.set_message(f'No "config system admin" block or admin users defined.')
            return False # Return False if there are no admin users to check

        # Ensure we are working with a list, even if there's only one admin.
        # fortios_xutils sometimes returns a single dict if there's only one entry.
        if not isinstance(config_system_admin_entries, list):
            config_system_admin_entries = [config_system_admin_entries] # Wrap single dict in a list

        fail = False
        if len(config_system_admin_entries) > 0:
            self.add_message('There are admin users defined:')
            for admin_entry in config_system_admin_entries: # Iterate directly over the list of admin entries
                # Each 'admin_entry' here is what you previously expected to be in 'edit'
                username = admin_entry.get("edit", "N/A") # Use .get() for safer access
                self.add_message(f'user: {username}')
                
                there_is_trusthost = False
                for key in admin_entry.keys(): # Iterate over keys in the current admin_entry
                    if key.startswith('trusthost'):
                        there_is_trusthost = True
                        # Ensure 'edit[key]' is a list before joining, or handle strings directly
                        # It's typical for fortios_xutils to return list of strings for multiple values
                        trusted_hosts_value = admin_entry[key]
                        if isinstance(trusted_hosts_value, list):
                            l = ' '.join(trusted_hosts_value)
                        else:
                            l = str(trusted_hosts_value) # Handle if it's a single string
                        self.add_message(f'set {key} {l}')
                
                if not there_is_trusthost:
                    self.add_message(f"Account '{username}' has no trusted hosts configured.")
                    fail = True
        else:
            self.set_message('There are no user defined (after processing config).')
            return False # No users to check, so it's not a failure for trusted hosts requirement if there are no accounts.

        return not fail # If 'fail' is True, then the check fails. If 'fail' is False, the check passes.
