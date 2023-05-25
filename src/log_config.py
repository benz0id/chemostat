import logging
import sys

import global_constants
basic_format_string = '%(levelname)s:%(name)s:%(message)s'
logging.basicConfig(filename='all_logs.log', level=logging.INFO,
                    format=basic_format_string)
basic_formatter = logging.Formatter(basic_format_string)

# Configure handler for unwanted behaviour.
err_handler = logging.FileHandler('logs/errors.log')
err_handler.setFormatter(basic_formatter)
err_handler.setLevel(logging.WARN)

print_handler = logging.StreamHandler(sys.stdout)
print_handler.setLevel(logging.INFO)
logging.root.addHandler(print_handler)
