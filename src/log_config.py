import logging
import sys
import src.global_constants


def get_basic_formatter() -> logging.Formatter:
    """Gets a basic logging formatter."""
    basic_format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    return logging.Formatter(basic_format_string)


def config_loggers() -> None:
    logging.basicConfig(filename='all_logs.log', level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    root_logger = logging.getLogger('root')
    root_logger.handlers = []
    root_logger.setLevel(logging.INFO)
    basic_handler = logging.FileHandler('all_logs.log')
    basic_handler.setLevel(logging.INFO)
    root_logger.addHandler(basic_handler)

    # Configure handler for unwanted behaviour.
    # err_handler = logging.FileHandler('logs/errors.log')
    # err_handler.setFormatter(get_basic_formatter())
    # err_handler.setLevel(logging.WARN)
    # root_logger.addHandler(err_handler)

    # print_handler = logging.StreamHandler(sys.stdout)
    # print_handler.setLevel(logging.INFO)
    # root_logger.addHandler(print_handler)

    # warn_handler = logging.StreamHandler(sys.stderr)
    # warn_handler.setLevel(logging.WARN)
    # root_logger.addHandler(warn_handler)
