from functools import wraps
from pathlib import PurePath


class Pather:
    """
    class InputFilePather(Pather):
        @staticmethod
        def get_constructor_kwargs(instance):
            return {'instance': instance}

        def __init__(self, instance):
            self.instance = instance

        def base(self):
            return PurePath(f'my_model/{self.instance.pk}/')

        def input_dir(self):
            return self.base() / PurePath('inputs')

        def input_file(self, instance, filename):
            return self.input_dir() / PurePath(filename)

    @InputFilePather.upload_to('input_file')
    def location_input():
        pass

    class UploadedFile(models.Model):
        content = FileField(blank=True, upload_to=location_input, max_length=1000)
    """
    @classmethod
    def make_upload_to_callable(cls, method):
        def f(instance, filename):
            kwargs = cls.get_constructor_kwargs(instance)
            pather = cls(**kwargs)
            path = getattr(pather, method)(instance, filename)
            return str(path)
        return f

    @classmethod
    def upload_to(cls, method):
        def decorator(h):
            @wraps(h)
            def f(instance, filename):
                callable = cls.make_upload_to_callable(method)
                return callable(instance, filename)
            return f
        return decorator

    @staticmethod
    def get_constructor_kwargs(instance):
        raise NotImplementedError

    def base(self):
        return PurePath('/')
