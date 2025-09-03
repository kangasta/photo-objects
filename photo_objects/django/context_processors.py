from importlib.metadata import PackageNotFoundError, version


class Metadata:
    def __init__(self):
        try:
            self.version = version('photo_objects')
        except PackageNotFoundError:
            self.version = None


def metadata(_):
    return {"photo_objects_metadata": Metadata()}
