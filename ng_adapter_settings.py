from nicegui import ui
from adapters import AdapterBase
from enum import Enum, EnumMeta

# region Logger
import os
from debug import get_logger
log = get_logger("adapters")
# endregion


async def adapter_settings_async(adapter):
    return adapter_settings(adapter)

def adapter_settings(adapter):
    log.info(f"Creating settings for adapter: {adapter.__class__}")
    settings = {}
    try:
        for name, a in adapter.ATTRIBUTES.items():
            log.info(f"Adding setting: {name} of type: {a['type']}")
            with ui.row():
                # print(a['type'], isinstance(a['type'], EnumMeta), issubclass(a['type'], EnumMeta))
                if a['type'] == str:
                    settings[name] = ui.input(name, value=a['default'])

                elif a['type'] == float or a['type'] == int:
                    if 'min' in a and 'max' in a:
                        ui.label(name)
                        settings[name] = ui.slider(min=a['min'], max=a['max'], value=a['default'], step=0.01)
                        # settings[name] = ui.number(name, value=a['default'])
                    else:
                        settings[name] = ui.number(name, value=a['default'])

                elif a['type'] == bool:
                    settings[name] = ui.switch(name, value=a['default'])

                elif issubclass(a['type'], EnumMeta) or isinstance(a['type'], EnumMeta):
                    options = {}
                    for e in a['type']:
                        options[e.value] = e.name
                    settings[name] = ui.select(options, value=list(options)[0], label=name)

                else:
                    log.warning(f"Unsupported adapter setting type by the UI: {name} - {a['type']}")

                if name in settings:
                    with settings[name]:
                        ui.tooltip(a['help'] if 'help' in a else "No description provided for this adapter.")
    except Exception as e:
        print("#"*1000)
        log.error(str(e), exc_info=True)
    
    log.info(f"Returning adapter_settings: {settings}")
    return settings
