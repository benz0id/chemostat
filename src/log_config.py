import logging

logger = logging.root
basic_formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')

# Configure handler for unwanted behaviour.
err_handler = logging.FileHandler('logs/errors.log')
err_handler.setFormatter(basic_formatter)
err_handler.setLevel(logging.WARN)