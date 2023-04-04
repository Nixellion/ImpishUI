#!/usr/bin/env python3
import asyncio
from nicegui import ui, Client
from ng_local_file_picker import local_file_picker
from ng_adapter_settings import adapter_settings
import adapters
import prompter
from database import Memory

# region Logger
import os
from debug import get_logger
log = get_logger(os.path.basename(os.path.realpath(__file__)))
# endregion

async def pick_file() -> None:
    result = await local_file_picker('~', multiple=True)
    ui.notify(f'You chose {result}')

contents = []
mem = Memory()


async def update(content: ui.column) -> None:
    content.clear()
    with content:  # use the context of each client to update their ui
        for record in mem.messages:
            with ui.card().tight().classes('w-full no-wrap') as card:
                ui.textarea(record['author'], value=record['text']).classes('text-sm m-2')
        await ui.run_javascript(f'window.scrollTo(0, document.body.scrollHeight)', respond=False)

# here we use our custom page decorator directly and just put the content creation into a separate function

def get_selected_adapter(adapter_dropdown):
    return adapters.available_adapters[adapter_dropdown.value].Adapter()

def convert_ui_settings(settings):
    s = {}
    for key, ui_element in settings.items():
        s[key] = ui_element.value
    return s

@ui.page('/')
async def index_page(client) -> None:
    async def send() -> None:
        chosen_textgen_adapter = get_selected_adapter(textgen_adapter)
        chosen_sum_adapter = get_selected_adapter(textgen_adapter)

        chosen_textgen_adapter.set_settings(convert_ui_settings(textgen_settings))
        chosen_sum_adapter.set_settings(convert_ui_settings(summarizer_settings))

        mem.add(user_prompt.value, "You", summarizer=chosen_sum_adapter)

        prompt = prompter.format_prompt(user_prompt=user_prompt.value)
        ai_response = chosen_textgen_adapter.generate(prompt)
        mem.add(ai_response, "Impish", summarizer=chosen_sum_adapter)

        user_prompt.value = ''
        await asyncio.gather(*[update(content) for content in contents])  # run updates concurrently

    # region Colors and Header
    ui.colors(primary='#1c1c1c', secondary='#53B689', accent='#faa300', positive='#53B689')

    with ui.header().classes('justify-between text-white'):
        ui.button(on_click=lambda: left_drawer.toggle()).props('flat color=white icon=menu')
        ui.label('ImpishUI').classes('font-bold')
        ui.button(on_click=lambda: right_drawer.toggle()).props('flat color=white icon=menu')
    # endregion

    # region Main Container
    with ui.row().classes('w-full'):
        # ui.button('Choose file', on_click=pick_file).props('icon=folder')

        await client.connected()  # update(...) uses run_javascript which is only possible after connecting
        contents.append(ui.column().classes('w-full max-w-4xl mx-auto'))  # save ui context for updates
        await update(contents[-1])  # ensure all messages are shown after connecting
    # endregion

    # region Drawers
    with ui.left_drawer() as left_drawer:

        text_generation_adapters = {}
        summarization_adapters = {}
        for adapter_name, adapter_module in adapters.available_adapters.items():
            if adapters.AdapterCapability.TEXT_GENERATION in adapter_module.CAPABILITIES:
                text_generation_adapters[adapter_name] = adapter_module.NAME
            if adapters.AdapterCapability.SUMMARIZATION in adapter_module.CAPABILITIES:
                summarization_adapters[adapter_name] = adapter_module.NAME

        text_generation_prompt_formats = {}
        for format in prompter.PromptFormat:
            text_generation_prompt_formats[format.value] = format.name

        async def textgen_ui_update() -> None:
            textgen_ui.clear()
            with textgen_ui:
                textgen_settings = adapter_settings(get_selected_adapter(textgen_adapter))

        textgen_adapter = ui.select(text_generation_adapters, value=list(summarization_adapters)[0], label='TextGen Adapter', on_change=textgen_ui_update)
        with ui.expansion(f"Textgen settings", icon='gear') as textgen_ui:
            textgen_settings = adapter_settings(get_selected_adapter(textgen_adapter))

        textgen_prompt_format = ui.select(text_generation_prompt_formats, value=20, label='TextGen Prompt Format')

        async def summarizer_ui_update() -> None:
            summarizer_ui.clear()
            with summarizer_ui:
                summarizer_settings = adapter_settings(get_selected_adapter(summarizer_adapter))

        summarizer_adapter = ui.select(summarization_adapters, value=list(summarization_adapters)[-1], label='Summarization Adapter', on_change=summarizer_ui_update)
        with ui.expansion(f"Summarizer settings", icon='gear') as summarizer_ui:
            summarizer_settings = adapter_settings(get_selected_adapter(summarizer_adapter))

    with ui.right_drawer() as right_drawer:
        ui.label('World Info')

    left_drawer.toggle()
    right_drawer.toggle()
    # endregion

    # region Footer
    with ui.footer(), ui.column().classes('w-full max-w-3xl mx-auto my-6'):
        with ui.row().classes('w-full no-wrap items-center'):
            user_prompt = ui.textarea(placeholder='Prompt').props('autofocus input-class=mx-3') \
                .classes('w-full self-center')
        ui.button("SEND", on_click=send)
    # endregion


from configuration import config
if config['nicegui']:
    ui.run(**config['nicegui'])
else:
    ui.run()
