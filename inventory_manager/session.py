_current_user = ""


def set_current_user(name):
    global _current_user
    _current_user = name


def get_current_user():
    return _current_user
