import logging
import sys
import src.global_constants


def get_basic_formatter() -> logging.Formatter:
    """Gets a basic logging formatter."""
    basic_format_string = '%(levelname)s:%(name)s:%(message)s'
    return logging.Formatter(basic_format_string)


def config_loggers() -> None:
    logging.basicConfig(filename='all_logs.log', level=logging.INFO,
                        format='%(levelname)s:%(name)s:%(message)s')

    root_logger = logging.getLogger('root')

    # Configure handler for unwanted behaviour.
    err_handler = logging.FileHandler('logs/errors.log')
    err_handler.setFormatter(get_basic_formatter())
    err_handler.setLevel(logging.WARN)
    root_logger.addHandler(err_handler)

    print_handler = logging.StreamHandler(sys.stdout)
    print_handler.setLevel(logging.INFO)
    root_logger.addHandler(print_handler)

    err_print_handler = logging.StreamHandler(sys.stderr)
    err_print_handler.setLevel(logging.ERROR)
    root_logger.addHandler(err_print_handler)
