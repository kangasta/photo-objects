from importlib.metadata import version


class Metadata:
    version = version('photo_objects')


def metadata(_):
    return {"photo_objects_metadata": Metadata()}
