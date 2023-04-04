from nicegui import ui
from adapters import AdapterBase
from enum import Enum, EnumMeta

# region Logger
import os
from debug import get_logger
log = get_logger(os.path.basename(os.path.realpath(__file__)))
# endregion

def adapter_settings(adapter: AdapterBase):
    settings = {}
    for name, a in adapter.ATTRIBUTES.items():
        with ui.row():
            print(a['type'], isinstance(a['type'], EnumMeta), issubclass(a['type'], EnumMeta))
            if a['type'] == str:
                settings[name] = ui.input(name, value=a['default'])

            elif a['type'] == float:
                if 'min' in a and 'max' in a:
                    # ui.slider(name, min=a['min'], max=a['max'], value=a['default'])
                    settings[name] = ui.number(name, value=a['default'])

            elif issubclass(a['type'], EnumMeta) or isinstance(a['type'], EnumMeta):
                options = {}
                for e in a['type']:
                    options[e.value] = e.name
                settings[name] = ui.select(options, value=list(options)[0], label=name)

            else:
                log.warning(f"Unsupported adapter setting type by the UI: {a['type']}")
    return settings
