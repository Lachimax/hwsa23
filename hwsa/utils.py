import os
import astropy.io.misc.yaml as yaml

debug = False


def debug_print(*args):
    if debug:
        print(*args)


def sanitise_file_ext(filename: str, ext: str):
    """
    Checks if the filename has the desired extension; adds it if not and returns the filename.
    :param filename: The filename.
    :param ext: The extension, eg '.fits'
    :return:
    """
    if ext[0] != '.':
        ext = '.' + ext
    length = len(ext)
    if filename[-length:] != ext:
        filename = filename + ext

    return filename


def save_params(file: str, dictionary: dict):
    file = sanitise_file_ext(filename=file, ext=".yaml")

    with open(file, 'w') as f:
        yaml.dump(dictionary, f)


def load_params(file: str):
    file = sanitise_file_ext(file, '.yaml')

    debug_print(2, 'Loading parameter file from ' + str(file))

    if os.path.isfile(file):
        with open(file) as f:
            p = yaml.load(f)
    else:
        p = None
        debug_print(1, 'No parameter file found at', str(file) + ', returning None.')
    return p


def mkdir_check(*paths: str):
    """
    Checks if a directory exists; if not, creates it.
    :param paths: each argument is a path to check and create.
    """
    for path in paths:
        if not os.path.isdir(path):
            debug_print(2, f"Making directory {path}")
            os.mkdir(path)
        else:
            debug_print(2, f"Directory {path} already exists, doing nothing.")
