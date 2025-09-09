from checker import Checker

class Check_CIS_4_2_3(Checker):

    def __init__(self, firewall, display, verbose=False):
        
        super().__init__(firewall, display, verbose)
        
        self.id = "4.2.3"
        self.title = "Enable Outbreak Prevention Database"
        self.levels = [2]
        self.auto = True
        self.benchmark_version = "v1.1.0"
        self.benchmark_author = "CIS"

    def do_check(self):
        # interfaces = self.firewall.get_interfaces() # This line is not used in the current logic, can be removed if truly not needed.
        av_profiles = self.firewall.get_av_profiles()
        
        nb_fail = 0
        for av_profile in av_profiles:
            # --- START OF FIX ---
            # Debugging: Print the current av_profile to understand its structure
            # self.display.debug(f"Processing av_profile: {av_profile.get('name', 'N/A')} - {av_profile}")

            if "configs" not in av_profile:
                # If 'configs' key is missing, this profile is not structured as expected for this check
                # Add a message to indicate this specific issue
                profile_name = av_profile.get('name', av_profile.get('edit', 'Perfil AV desconocido'))
                self.add_message(f'AV profile "{profile_name}" is missing the expected "configs" section. Cannot perform check.')
                # Optionally, you might want to count this as a failure or simply skip it.
                # For now, we'll just log and skip, not incrementing nb_fail directly for this structural error.
                continue # Skip to the next av_profile
            # --- END OF FIX ---

            for config in av_profile["configs"]:
                if "outbreak-prevention" not in config.keys():
                    self.add_message(f'outbreak-prevention not defined in A/V policy "{av_profile["edit"]}" for {config["config"]}')
                    nb_fail += 1
                elif config["outbreak-prevention"] != "block":
                    self.add_message(f'outbreak-prevention not blocking in A/V policy "{av_profile["edit"]}" for {config["config"]}')
                    nb_fail += 1
        
        # Display results
        self.add_message(f'{nb_fail} policies have no A/V outbreak protection')
            
        return nb_fail == 0