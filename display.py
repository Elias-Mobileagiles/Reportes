# display.py

import sys

class Display:
    # MODIFIED: __init__ to accept verbose and quiet
    def __init__(self, verbose=False, quiet=False):
        self.verbose = verbose
        self.quiet = quiet

    def show(self, text, end='\n'):
        """
        Displays content directly, typically for interactive prompts or important messages.
        Includes existing indentation.
        """
        if isinstance(text, list):
            for line in text:
                print(f'\t| {line}', end=end)
        else:
            print(f'\t| {text}', end=end)

    def ask(self, question_context, question):
        """Asks a question and returns the user's answer, respecting existing formatting."""
        
        print("") # Go to new line
        self.show('--------------[ Question ] --------------------')
        if question_context is not None:
            self.show(question_context)
        
        # If in quiet mode, don't wait for input, provide a default answer
        if self.quiet:
            # We still show the question for logging/context, but provide an automatic 'y'
            self.show(f'{question} : (Auto-answered \'y\' in quiet mode)')
            answer = "y" # Default to 'yes' in quiet mode
        else:
            self.show(f'{question} :', end='')
            answer = input()
            
        self.show('-----------------------------------------------')
        return answer

    # NEW: Added log method to handle various log levels and verbosity
    def log(self, message, log_level="INFO"):
        """
        Logs a message to the console based on verbosity and quiet settings.
        Adds color coding for better visibility of important messages.
        
        Args:
            message (str): The message to log.
            log_level (str): The level of the log (e.g., "INFO", "WARN", "FAIL", "PASS", "DEBUG", "ERROR").
        """
        should_display = False
        
        # Determine if the message should be displayed
        if self.quiet:
            # In quiet mode, only display critical messages
            if log_level in ["FAIL", "ERROR", "WARN"]:
                should_display = True
            # For PASS, if a summary is desired in quiet mode, enable here
            # elif log_level == "PASS" and not self.verbose: # Maybe show PASS in quiet if it's a final summary
            #     should_display = True
        elif self.verbose:
            # In verbose mode, display everything
            should_display = True
        else:
            # Default mode: display INFO, WARN, FAIL, PASS, ERROR
            if log_level in ["INFO", "WARN", "FAIL", "PASS", "ERROR"]:
                should_display = True
        
        if should_display:
            # Use ANSI escape codes for colors
            color_start = ""
            color_end = "\033[0m" # Reset color
            output_stream = sys.stdout

            if log_level == "FAIL":
                color_start = "\033[91m" # Red
                output_stream = sys.stderr
            elif log_level == "ERROR":
                color_start = "\033[91m" # Red
                output_stream = sys.stderr
            elif log_level == "WARN":
                color_start = "\033[93m" # Yellow
            elif log_level == "PASS":
                color_start = "\033[92m" # Green
            elif log_level == "DEBUG":
                color_start = "\033[90m" # Grey (less prominent)

            # Print the message with color and the specific log level prefix
            print(f"{color_start}[{log_level}] {message}{color_end}", file=output_stream)
