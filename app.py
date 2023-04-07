#!/usr/bin/env python3
"""
TODO:

- [x] Reading and Editing modes


- [ ] Per-paragraph generation, generate multiple paragraphs.
- [ ] "Processing" state, locking UI and showing progress spinner or bar
- [ ] Savegames UI, selecting and adding games
- [ ] Remember settings (broken)
- [ ] Story export options (formats, plaintext or smth)
- [ ] Separate dedicated summarizer editor
- [ ] Filtering of text

- [ ] AND CHECK TODO, FIXME, BUG AND OTHER TAGS IN THE PROJECT (VSCODE TODOs extension or PyCharm can list them)
"""

import asyncio
from nicegui import ui, Client
from ng_local_file_picker import local_file_picker
from ng_adapter_settings import adapter_settings, adapter_settings_async
import adapters
import prompter
import database
from database import Game, Settings, Message, Character
from functools import partial
from datetime import datetime
from werkzeug.utils import secure_filename
from state import State

from paths import APP_DIR
from configuration import config

from notifier import notify_sound


# region Logger
import os
from debug import get_logger
log = get_logger(os.path.basename(os.path.realpath(__file__)))
# endregion


# async def pick_file() -> None:
#     result = await local_file_picker('~', multiple=True)
#     ui.notify(f'You chose {result}')

async def export_game() -> None:
    export_filepath = os.path.join(APP_DIR, "data", secure_filename("game_export_{}_{}.txt".format(
        State.instance.LOADED_GAME.name, datetime.now().strftime(r"%Y_%m_%d_%H_%M_%S"))))
    with open(export_filepath, "w+", encoding="utf-8") as f:
        f.write(State.instance.LOADED_GAME.all_text)
    ui.notify(f'Game exported to {export_filepath}')


# contents = []
# chat_container = None
database.load_game(1)

# here we use our custom page decorator directly and just put the content creation into a separate function

def get_selected_adapter(adapter_dropdown):
    log.debug(f"Get selected adapter: {adapter_dropdown}")
    return adapters.available_adapters[adapter_dropdown.value].Adapter()


def convert_ui_settings(settings):
    log.info(f"convert_ui_settings: {settings}")
    s = {}
    for key, ui_element in settings.items():
        s[key] = ui_element.value
    return s


# @ui.page('/')
# async def index_page(client) -> None:
# Yeah, NiceGUI while nice has it's quirks, like heavy context dependence, and so far I didn't find a way to move these functinos outside of this route function. But it works and looks fine for now.
async def update_memory_text(message_id, textarea) -> None:
    log.info(f"update_memory_text {message_id}.")
    State.instance.BUSY = True
    State.instance.progress_spinner.visible = True
    update_selected_adapaters()
    message = Message.select().where(Message.id == message_id).get()
    message.text = textarea.value
    message.save()
    State.instance.BUSY = False
    State.instance.progress_spinner.visible = False
    await reload_chat()

async def update_memory_summary_text(message_id, textarea) -> None:
    log.info(f"update_memory_summary_text {message_id}.")
    State.instance.BUSY = True
    State.instance.progress_spinner.visible = True
    update_selected_adapaters()
    message = Message.select().where(Message.id == message_id).get()
    message.summary = textarea.value
    message.save()
    State.instance.BUSY = False
    State.instance.progress_spinner.visible = False
    await reload_chat()

async def rerun_memory_summarizer(message_id) -> None:
    log.info(f"rerun_memory_summarizer {message_id}.")
    State.instance.BUSY = True
    State.instance.progress_spinner.visible = True
    update_selected_adapaters()
    message = Message.select().where(Message.id == message_id).get()
    message.summarize()
    message.save()
    State.instance.BUSY = False
    State.instance.progress_spinner.visible = False
    notify_sound()
    await reload_chat()



async def change_tokenizer() -> None:
    State.instance.TOKENIZER = tokenizer_name.value


async def delete_memory_text(message_id) -> None:
    log.info(f"Deleting message {message_id}.")
    message = Message.select().where(Message.id == message_id).get()
    message.delete_instance()
    await reload_chat()


async def reload_chat() -> None:
    if not chat_container:
        log.warning("Chat container not initialized yet.")
        return
    chat_container.clear()
    chat_container_read.clear()
    with chat_container:  # use the context of each client to update their ui
        for record in State.instance.LOADED_GAME.messages:
            with ui.card().tight().classes('w-full no-wrap') as card:
                textarea = ui.textarea(record.author, value=record.text).classes('text-sm m-2')
                summary_textarea = ui.textarea("Summary", value=f"{record.summary}").classes('text-sm m-2')
                update_button = ui.button("Update Text", on_click=partial(update_memory_text, record.id, textarea))
                update_summary_button = ui.button("Update Summary", on_click=partial(update_memory_summary_text, record.id, summary_textarea))
                rerun_summarizer_button = ui.button("Rerun Summarizer", on_click=partial(rerun_memory_summarizer, record.id))
                delete_button = ui.button("Delete", on_click=partial(delete_memory_text, record.id))
        # await ui.run_javascript(f'window.scrollTo(0, document.body.scrollHeight)', respond=False)
    with chat_container_read:  # use the context of each client to update their ui
        for record in State.instance.LOADED_GAME.messages:
            with ui.card().tight().classes('w-full no-wrap') as card:
                markdown = ui.html(record.text.replace("\n", "<br>")).classes('text-sm m-2')
        # await ui.run_javascript(f'window.scrollTo(0, document.body.scrollHeight)', respond=False)


def update_selected_adapaters():
    log.debug("# update_selected_adapaters...")
    log.debug("# get_selected_adapters...")
    State.instance.chosen_textgen_adapter = get_selected_adapter(textgen_adapter)
    State.instance.chosen_sum_adapter = get_selected_adapter(summarizer_adapter)
    State.instance.chosen_wi_extractor_adapter = get_selected_adapter(wi_extractor_adapter)

    log.debug("# set_settings...")
    State.instance.chosen_textgen_adapter.set_settings(convert_ui_settings(State.instance.textgen_settings))
    State.instance.chosen_sum_adapter.set_settings(convert_ui_settings(State.instance.summarizer_settings))
    State.instance.chosen_wi_extractor_adapter.set_settings(convert_ui_settings(State.instance.wi_extractor_settings))

    log.debug("# State.instance.LOADED_GAME.summarizer = ...")
    State.instance.LOADED_GAME.summarizer = summarizer_adapter.value
    State.instance.LOADED_GAME.save()

    log.debug("# State.instance.SUM_ADAPTER = ...")
    State.instance.SUM_ADAPTER = State.instance.chosen_sum_adapter
    State.instance.TEMPLATE_NAME = textgen_prompt_format.value
    

# TODO: This should be handled as "Heavy computation" https://github.com/zauberzeug/nicegui/blob/main/examples/progress/main.py


async def send() -> None:
    if State.instance.BUSY:
        log.warning("Server is still busy processing previous request!")
        return
    State.instance.BUSY = True
    State.instance.progress_spinner.visible = True
    final_ai_response = None
    ai_response = None
    message = None
    print()
    log.message("#"*80)
    for i in range(0, int(paragraphs_to_generate.value)):
        log.message(f"PARAGRAPH {i}...")
        try:
            update_selected_adapaters()
            auto_world_info_entities = State.instance.LOADED_GAME.get_automatic_world_info()
            prompt = prompter.format_prompt(
                user_prompt=user_prompt.value if not ai_response else final_ai_response,
                summary=State.instance.LOADED_GAME.ai_summary_entries if summary_only_ai_messages.value else State.instance.LOADED_GAME.all_summary_entries,
                world_info=world_info.value,
                auto_world_info_entities=auto_world_info_entities,
                instruction=instruction.value,
                max_tokens=State.instance.chosen_textgen_adapter.get_max_tokens(),
                max_history_tokens=max_history_tokens.value,
                history=State.instance.LOADED_GAME.all_text
            )
            
            log.message(f"PROMPT: {prompt}")

            ai_response = State.instance.chosen_textgen_adapter.generate(prompt)
            if final_ai_response is None:
                final_ai_response = ai_response
            else:
                final_ai_response += "\n\n" + ai_response.strip()

            
            log.message("="*80)
            log.message(f"RESPONSE: {ai_response}")

            user_prompt.value = ''
        except Exception as e:
            log.error(e, exc_info=True)
    

    State.instance.LOADED_GAME.add_message(user_prompt.value, "You")
    message = State.instance.LOADED_GAME.add_message(final_ai_response.strip(), "Impish")

    
    

    log.message("#"*80)
    print()
    
    State.instance.BUSY = False
    State.instance.progress_spinner.visible = False
    notify_sound()
    await reload_chat()
    # await asyncio.gather(*[reload_chat(content) for content in contents])  # run updates concurrently

# region Colors and Header
ui.colors(primary='#faa300', secondary='#53B689', accent='#faa300', positive='#53B689')

with ui.header().classes('justify-between text-white').style('background-color: #1c1c1c'):
    ui.button(on_click=lambda: left_drawer.toggle()).props('flat color=white icon=menu')
    ui.label('ImpishUI').classes('font-bold')
    ui.button(on_click=lambda: right_drawer.toggle()).props('flat color=white icon=menu')
# endregion

# region Main Container
# await client.connected()
with ui.tabs().classes('w-full') as tabs:
    ui.tab("Read")
    ui.tab("Edit")

with ui.tab_panels(tabs, value='Read').classes('w-full').style('background-color: rgba(0,0,0,0)'):
    with ui.tab_panel('Read').classes('w-full'):
        chat_container_read = ui.column().classes('w-full max-w-4xl mx-auto')
    with ui.tab_panel('Edit').classes('w-full'):
        chat_container = ui.column().classes('w-full max-w-4xl mx-auto')
    # ui.button('Choose file', on_click=pick_file).props('icon=folder')

        # update(...) uses run_javascript which is only possible after connecting

    # contents.append(ui.column().classes('w-full max-w-4xl mx-auto'))  # save ui context for updates
    asyncio.run(reload_chat())  # ensure all messages are shown after connecting

State.instance.progress_spinner = ui.spinner()
State.instance.progress_spinner.visible = False
# endregion

# region Drawers
with ui.left_drawer() as left_drawer:

    text_generation_adapters = {}
    summarization_adapters = {}
    wi_extractor_adapters = {}
    for adapter_name, adapter_module in adapters.available_adapters.items():
        if adapters.AdapterCapability.TEXT_GENERATION in adapter_module.CAPABILITIES:
            text_generation_adapters[adapter_name] = adapter_module.NAME
        if adapters.AdapterCapability.SUMMARIZATION in adapter_module.CAPABILITIES:
            summarization_adapters[adapter_name] = adapter_module.NAME
        if adapters.AdapterCapability.WORLD_INFO_EXTRACTION in adapter_module.CAPABILITIES:
            wi_extractor_adapters[adapter_name] = adapter_module.NAME

    # region Textgen Settings
    async def textgen_ui_update() -> None:
        textgen_ui.clear()
        with textgen_ui:
            State.instance.textgen_settings = await adapter_settings_async(get_selected_adapter(textgen_adapter))
        with textgen_adapter:
            docstring = get_selected_adapter(textgen_adapter).__doc__
            ui.tooltip(docstring if docstring else "No description provided for this adapter.")

    textgen_adapter = ui.select(text_generation_adapters, value=list(summarization_adapters)[
                                0], label='TextGen Adapter', on_change=textgen_ui_update)
    with ui.expansion(f"Textgen settings", icon='gear') as textgen_ui:
        State.instance.textgen_settings = adapter_settings(get_selected_adapter(textgen_adapter))

    textgen_prompt_format = ui.select(prompter.get_all_formats(), value=prompter.get_all_formats()[
                                      0], label='TextGen Prompt Format')
    # endregion

    # region Summarizer UI
    async def summarizer_ui_update() -> None:
        summarizer_ui.clear()
        with summarizer_ui:
            State.instance.summarizer_settings = await adapter_settings_async(get_selected_adapter(summarizer_adapter))
        with summarizer_adapter:
            docstring = get_selected_adapter(summarizer_adapter).__doc__
            ui.tooltip(docstring if docstring else "No description provided for this adapter.")

    summarizer_adapter = ui.select(summarization_adapters, value=list(
        summarization_adapters)[0], label='Summarization Adapter', on_change=summarizer_ui_update)

    with ui.expansion(f"Summarizer settings", icon='gear') as summarizer_ui:
        State.instance.summarizer_settings = adapter_settings(get_selected_adapter(summarizer_adapter))
    tokenizer_name = ui.select(config['tokenizers'], value=list(
        config['tokenizers'])[0], label='Tokenizer', on_change=change_tokenizer)
    # endregion

    # region World Info Extractor UI
    async def wi_extractor_ui_update() -> None:
        wi_extractor_ui.clear()
        with wi_extractor_ui:
            State.instance.wi_extractor_settings = await adapter_settings_async(get_selected_adapter(wi_extractor_adapter))
        with wi_extractor_adapter:
            docstring = get_selected_adapter(wi_extractor_adapter).__doc__
            ui.tooltip(docstring if docstring else "No description provided for this adapter.")

    wi_extractor_adapter = ui.select(wi_extractor_adapters, value=list(
        wi_extractor_adapters)[0], label='WI Extractor Adapter', on_change=wi_extractor_ui_update)

    with ui.expansion(f"WI Extractor Settings", icon='gear') as wi_extractor_ui:
        State.instance.wi_extractor_settings = adapter_settings(get_selected_adapter(wi_extractor_adapter))

    # endregion

    summary_only_ai_messages = ui.switch("Include only AI messages in summary", value=False)
    paragraphs_to_generate = ui.number("Pargraphs to generate", value=3)

    with ui.row():
        ui.label("Max history tokens:")
        max_history_tokens_label = ui.label("")
    max_history_tokens = ui.slider(value=512, min=0, max=2048).bind_value_to(max_history_tokens_label, "text")

    # export_game_button = ui.button('Export Game', on_click=export_game).props('icon=folder')
    ui.button('Export Game', on_click=export_game).props('icon=folder')

    asyncio.run(textgen_ui_update())
    asyncio.run(summarizer_ui_update())

with ui.right_drawer() as right_drawer:
    instruction = ui.textarea("Instruction", value="Continue writing a story")
    world_info = ui.textarea("World Info")

left_drawer.toggle()
right_drawer.toggle()
# endregion

# region Footer
with ui.footer().style('background-color: #1c1c1c'), ui.column().classes('w-full max-w-3xl mx-auto my-6'):
    with ui.row().classes('w-full no-wrap items-center'):
        user_prompt = ui.textarea(placeholder='Prompt').props('autofocus input-class=mx-3') \
            .classes('w-full self-center')
    ui.button("SEND", on_click=send)
# endregion


if config['nicegui']:
    ui.run(**config['nicegui'])
else:
    ui.run()
