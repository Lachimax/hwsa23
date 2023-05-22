import astropy.io.misc.yaml as yaml


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
