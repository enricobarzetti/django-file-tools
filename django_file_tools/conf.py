from dataclasses import dataclass
from typing import Any

from django.conf import settings as django_settings

settings_prefix = "FILE_TOOLS_"


@dataclass(frozen=True)
class AppSettings:
    FILE_TOOLS_TEMP_FOLDER_PREFIX: str = 'temp'

    def __getattribute__(self, __name: str) -> Any:
        """
        Check if a Django project settings should override the app default.

        In order to avoid returning any random properties of the django settings, we inspect the prefix firstly.
        """

        if __name.startswith(settings_prefix) and hasattr(django_settings, __name):
            return getattr(django_settings, __name)

        return super().__getattribute__(__name)


app_settings = AppSettings()
