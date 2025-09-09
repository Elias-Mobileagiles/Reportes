#!/usr/bin/env python3
import json
import checks
import firewall
import display
import argparse
from pathlib import Path
from json import JSONDecodeError
import fortios_xutils.parser
import os
import shutil
from fpdf import FPDF

parser = argparse.ArgumentParser(description='Apply a benchmark to a Fortigate configuration file. \
        Example: fortigate-security-auditor.py -q -o results.csv -l 1 2 -w WAN1 WAN2 --autofix firewall.conf')
parser.add_argument('-q', '--quiet', help='Not interactive: ignore manual steps', action='store_true')
parser.add_argument('-v', '--verbose', help='Increase verbosity', action='store_true')
parser.add_argument('-j', '--json', help='Input file is json already parsed by fortios_xutils', action='store_true')
parser.add_argument('-o', '--output', help='Output PDF File (e.g., results.pdf)')
parser.add_argument('-l', '--levels', help='Levels to check. (default: 1)', nargs='+', default="1")
parser.add_argument('-i', '--ids', help='Checks id to perform. (default: all if applicable)', nargs='+', default=None)
parser.add_argument('-c', '--resume', help='Resume an audit that was already started. Automatic items are re-checked but manually set values are retrieved from cache.', action='store_true')
parser.add_argument('-w', '--wan', help='List of wan interfaces separated by spaces (example: --wan port1 port2)', nargs='+', default=None)
parser.add_argument('--interfaces', help='Show list of interfaces and exit', action='store_true')
parser.add_argument('--zones', help='Show list of zones and exit', action='store_true') # CORRECTED LINE
parser.add_argument('--autofix', help='Automatically try to fix errors in input file', action='store_true')
parser.add_argument('config', help='Configuration file exported from the fortigate or fortimanager', nargs=1)
# --- NUEVOS ARGUMENTOS ---
parser.add_argument('--report-name', help='Name for the report title (e.g., FortiGate alias)', default='Fortigate')
parser.add_argument('--report-date', help='Date for the report title (e.g., YYYY-MM-DD)', default='')
# --- FIN NUEVOS ARGUMENTOS ---
args = parser.parse_args()

filepath = args.config[0]
verbose = args.verbose
quiet = args.quiet
outputfile = args.output
report_name = args.report_name # Captura el nombre del reporte
report_date = args.report_date # Captura la fecha del reporte

# --- MODIFICACIÓN INICIO ---
# Check if the input file has a .txt extension and rename it to .conf
if filepath.lower().endswith('.txt'):
    new_filepath = filepath.replace('.txt', '.conf')
    try:
        os.rename(filepath, new_filepath)
        print(f"[+] Renamed input file from '{filepath}' to '{new_filepath}'")
        filepath = new_filepath # Update filepath to the new .conf file
    except OSError as e:
        print(f"[!] Error renaming file: {e}")
        exit(-1)
# --- MODIFICACIÓN FIN ---

cache_file_path = str(Path.home()) + '/.cache/fortigate-security-auditor.json'

# Create/Open cache file
if not os.path.exists(cache_file_path):
    if args.resume:
        print(f'[!] Cannot resume this benchmark because there is no cache file')
        exit(-1)
    else:
        print(f'[!] Creating local cache file in {cache_file_path}')
        cache_file = open(cache_file_path, mode='a')
        cache_file.write("{}")
        cache_file.close()
cache_file = open(cache_file_path, "r+")
cache = json.load(cache_file)
cache_file.close()
    
if not filepath in cache.keys():
    # There is no cache for this fortigate configuration file
    if args.resume:
        print(f'[!] Cannot resume this benchmark because there is no cache results for config {filepath}')
        exit(-1)
    cached_results = {}
else:
    cached_results = cache[filepath]

# Load fortigate configuration file
print(f'[+] Configuration file: {filepath}')

if args.json:
    f = open(filepath)
    config = json.load(f)["configs"]
    f.close()
    print(f'[+] Configuration loaded from JSON file')
else:
    # --- INICIO DE LA MODIFICACIÓN ---
    # Asegúrate de que el directorio 'tmp' exista en el mismo lugar que el script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    tmp_dir = os.path.join(script_dir, 'tmp')

    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir) # Esto crea el directorio (y los subdirectorios si son necesarios)
        print(f'[+] Created temporary directory: {tmp_dir}')
    # --- FIN DE LA MODIFICACIÓN ---
    
    reparse = True
    # Usa os.path.join para construir la ruta del archivo temporal de forma segura
    tmp_filepath = os.path.join(tmp_dir, os.path.basename(filepath))
    shutil.copyfile(filepath, tmp_filepath)
    
    while reparse:
        try:
            # Check non unicode characters. This will trigger an exception and we will be able to fix the file
            with open(tmp_filepath, 'r') as file :
                    filedata = file.read()
                    file.close()
                    
            # Try parsing
            parsed_output = fortios_xutils.parser.parse_show_config_and_dump(tmp_filepath, "tmp")
            reparse = False
            os.remove(tmp_filepath)
        except TypeError as e:
            if str(e) == "dict() got multiple values for keyword argument 'config'":
                print(f'[!] It seems you ran into bug https://github.com/ssato/python-anyconfig-fortios-backend/issues/3')
                print(f'     I can try to apply a dirty fix by replacing the following configuration block:')
                print(f'       config loggrp-permission')
                print(f'       set config read')
                print(f'       end')
                print(f'     by:')
                print(f'       config loggrp-permission')
                print(f'       set configxxx read')
                print(f'       end')
                print(f'     It may fail some checks that would evaluate this configuration items.')
                if args.autofix:
                    print(f'[+] Trying to fix the issue')
                else:
                    print(f'[?] Type \'yes\' to continue or Ctrl-C to quit')
                    while input() != "yes":
                        print(f'[?] Type \'yes\' to continue or Ctrl-C to quit')
                
                # Fix the set config read issue             
                with open(tmp_filepath, 'r') as file :
                    filedata = file.read()
                filedata = filedata.replace('set config read', 'set configxxx read')
                with open(tmp_filepath, 'w') as file:
                    file.write(filedata)
                    
                reparse = True
        except UnicodeDecodeError as e: # FIX: This was previously mis-indented
            print(f'[!] Parsing failed due to characters not utf-8 encoded')
            print(f'     I can try to remove those characters and re-parse again')
            print(f'     Most of the time, non utf-8 characters are in comments or non critical items, however that may fail some checks.')
            if args.autofix:
                print(f'[+] Trying to fix the issue')
            else:
                print(f'[?] Type \'yes\' to continue or Ctrl-C to quit')
                while input() != "yes":
                    print(f'[?] Type \'yes\' to continue or Ctrl-C to quit')
                
            # Fix the encoding
            with open(tmp_filepath, 'r', encoding='utf-8', errors='ignore') as file :
                    filedata = file.read()
                    file.close()
            with open(tmp_filepath, 'w') as file:
                    file.write(filedata)
            reparse = True
        
    config = parsed_output[1]["configs"]
    print(f'[+] Configuration succesfully parsed')

print(f'[+] Starting checks for levels: {",".join(args.levels)}')

if args.ids is not None:
    print(f'[+] Limiting to checks {", ".join(args.ids)}')

# Display object
display = display.Display()

# Firewall object
firewall = firewall.Firewall(config, display)
if args.wan is not None:
    print(f'[+] Configuring WAN interfaces: {", ".join(args.wan)}')
    firewall.set_wan_interfaces(args.wan)

# Display interfaces
if args.interfaces:
    print(f'[+] The following interfaces exist on the firewall:')
    for interface in firewall.get_interfaces():
        print(f'[-] {interface["edit"]}')
        if "vdom" in interface.keys() : print(f'     | vdom {interface["vdom"]}') 
        if "type" in interface.keys() : print(f'     | type {interface["type"]}')
        if "status" in interface.keys() : print(f'     | status {interface["status"]}')
        if "ip" in interface.keys() : 
            ips = ", ".join(interface["ip"])
            print(f'     | ip {ips}')
    exit(0)

# Display interfaces
if args.zones:
    print(f'[+] The following zones exist on the firewall:')
    for zone in firewall.get_zones():
        print(f'[-] {zone["edit"]}')
        if "interface" in zone.keys() : 
            if isinstance(zone["interface"], list):
                child_interfaces = ", ".join(zone["interface"])
            else:
                child_interfaces = zone["interface"]
            print(f'     | interfaces {child_interfaces}')
    exit(0)

# Instantiate checkers
performed_checks = []

checkers = [check_class(firewall, display, verbose) for check_class in checks.classes()]
for checker in checkers:
    if not checker.is_valid():
        continue

    if args.ids is not None and checker.get_id() not in args.ids:
        continue

    if checker.enabled and checker.is_level_applicable(args.levels):         
        if checker.auto:
            checker.run()
        else:
            if quiet:
                checker.skip()
            else:
                if args.resume:
                    if checker.get_id() in cached_results.keys():
                        # There is a cached result for this check
                        # IMPORTANT: Ensure the cached_results dictionary structure matches your Checker's restore_from_cache method
                        # 'message' (old) -> 'messages' (detailed list)
                        # New: 'current_summary_message' (for the main summary message)
                        # New: 'log_messages' (for the structured log entries)
                        cached_data = cached_results[checker.get_id()]
                        
                        # Adjusting the cached_data to match Checker's expectations if the cache is old
                        if "message" in cached_data and "messages" not in cached_data:
                            cached_data["messages"] = [cached_data["message"]] if not isinstance(cached_data["message"], list) else cached_data["message"]
                            del cached_data["message"]
                        
                        if "final_summary_message" in cached_data and "current_summary_message" not in cached_data:
                            cached_data["current_summary_message"] = cached_data["final_summary_message"]
                            del cached_data["final_summary_message"]

                        if "log_messages" not in cached_data:
                            # Attempt to reconstruct log_messages if they're missing but 'messages' exists
                            if "messages" in cached_data and cached_data["messages"]:
                                cached_data["log_messages"] = [{"message": msg, "level": "INFO"} for msg in cached_data["messages"]]
                            else:
                                cached_data["log_messages"] = []

                        checker.restore_from_cache(cached_data)
                    else:
                        # There is no cached result, we have to perform the step
                        checker.run()
                else:
                    checker.run()
        performed_checks.append(checker)

        # Save to cache - THIS IS THE CRITICAL LINE TO CHANGE
        # Using checker.messages for the list of detailed logs
        # Using checker.current_summary_message for the single summary message
        # Using checker.log_messages for the structured log entries
        cached_results[checker.get_id()] = {
            "result": checker.result,
            "messages": checker.messages,                   # Corrected to 'messages' (plural)
            "current_summary_message": checker.current_summary_message, # New attribute for the single summary message
            "log_messages": checker.log_messages,           # New attribute for structured logs
            "question": checker.question,
            "question_context": checker.question_context,
            "answer": checker.answer
        }

print('[+] Finished')
print('------------------------------------------------')
print('[+] Here is a summary:')

for performed_check in performed_checks:
    print(f'[{performed_check.get_id()}]\t[{performed_check.result}]\t{performed_check.title}')

# Save cache file
cache[filepath] = cached_results
cache_file = open(cache_file_path, "w")
json.dump(cache, cache_file, indent=4) # Added indent for readability
cache_file.close()

# Export to PDF
if outputfile is not None:
    print('------------------------------------------------')
    # Ensure the output file has a .pdf extension
    if not outputfile.lower().endswith('.pdf'):
        outputfile = f"{outputfile}.pdf"

    print(f'[+] Exporting results to {outputfile}')
    
    pdf = FPDF(orientation='L') # Changed to landscape orientation
    pdf.add_page()
    pdf.set_font("Arial", size=10)

    # --- MODIFICACIÓN DEL TÍTULO DEL PDF ---
    # Construye el título del reporte
    report_title = f"Fortigate Security Audit Report for {report_name}"
    if report_date:
        report_title += f" ({report_date})"

    # Add the dynamic title to the PDF
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, txt=report_title, ln=True, align='C')
    pdf.ln(10) # Add some space
    # --- FIN MODIFICACIÓN DEL TÍTULO DEL PDF ---

    # Set font for table headers
    pdf.set_font("Arial", 'B', 10)
    # Define column widths (adjust as needed for your data and page size)
    col_widths = [20, 15, 74, 10, 156] # Adjusted for wider landscape page. Total around 275mm
    headers = ["ID", "Result", "Check Title", "LVL", "Log Details"] # Changed header to 'Log Details'
    
    # Add headers to PDF table
    for header, width in zip(headers, col_widths):
        pdf.cell(width, 10, header, border=1, align='C') # Centered headers
    pdf.ln() # Move to next line after headers

    # Set font for table content
    pdf.set_font("Arial", size=8)
    for performed_check in performed_checks:
        # Get the full log, which now includes the summary message and detailed logs
        full_log_content = performed_check.get_log().replace('"', '\'').replace('\n', ' ')
        levels = ", ".join(str(x) for x in performed_check.levels)
        
        # Calculate height for multi_cell content
        # Estimate needed height for the multi_cell by breaking the text and summing line heights
        # This is an approximation; fpdf doesn't have a direct method to get future multi_cell height easily.
        # A more robust solution might involve creating a dummy PDF and calculating, but for simplicity:
        text_width = col_widths[4] - pdf.c_margin * 2 # Usable width for text
        lines = pdf.get_string_width(full_log_content) / text_width
        line_height = pdf.font_size * 1.2 # Standard line height based on font size
        
        # Ensure minimum height for row if log is empty or very short
        cell_height = max(10, lines * line_height) 

        # Store current Y position
        current_y = pdf.get_y()

        # Check if new page is needed for the multi_cell
        if current_y + cell_height > pdf.page_break_trigger:
            pdf.add_page()
            # If a new page is added, re-add headers for the new page for continuity
            pdf.set_font("Arial", 'B', 10)
            for header, width in zip(headers, col_widths):
                pdf.cell(width, 10, header, border=1, align='C')
            pdf.ln()
            pdf.set_font("Arial", size=8) # Reset font for content
            current_y = pdf.get_y() # Update current Y

        # Print cells for fixed-height columns
        pdf.cell(col_widths[0], cell_height, performed_check.get_id(), border=1, ln=0)
        pdf.cell(col_widths[1], cell_height, performed_check.result, border=1, ln=0)
        pdf.cell(col_widths[2], cell_height, performed_check.title, border=1, ln=0)
        pdf.cell(col_widths[3], cell_height, levels, border=1, ln=0)
        
        # Save X,Y for multi_cell
        x_log = pdf.get_x()
        y_log = pdf.get_y()

        # Print multi_cell content
        pdf.multi_cell(col_widths[4], line_height, full_log_content, border=1, align='L')
        
        # After multi_cell, restore Y position to the max height of the row for the next row
        pdf.set_xy(x_log + col_widths[4], current_y + cell_height) # Move to the end of the current line, adjusted for cell height
        pdf.ln() # Move to the next line for the next check

    pdf.output(outputfile) # Save the PDF
    print('[+] PDF report generated successfully.')