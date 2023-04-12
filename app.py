#!/usr/bin/env python3
"""
TODO:

- [x] Reading and Editing modes
- [x] Per-paragraph generation, generate multiple paragraphs.
- [x] Separate dedicated summarizer editor
- [x] Generating in multiple passes, and choosing one with best coherence score

- [ ] Consider adding-using this: https://github.com/chatarena/chatarena
- [ ] Consider using this if it's faster-lighter-better: https://stackoverflow.com/questions/60515107/calculating-semantic-coherence-in-a-given-speech-transcript
- [ ] "Processing" state, locking UI and showing progress spinner or bar
- [ ] Savegames UI, selecting and adding games
- [ ] Remember settings (broken)
- [ ] Story export - more options (formats, plaintext or smth)

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

database.load_game(1)
# region Main UI functions
# TODO Separate async vs non async or smth


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


# here we use our custom page decorator directly and just put the content creation into a separate function

from copy import copy


def get_selected_adapter(adapter_dropdown):
    log.debug(f"Get selected adapter: {adapter_dropdown}")
    return adapters.available_adapters[adapter_dropdown.value].Adapter()


def convert_ui_settings(settings):
    log.debug(f"convert_ui_settings: {settings}")
    s = {}
    for key, ui_element in settings.items():
        s[key] = ui_element.value
    log.debug(f"Converted settings: {s}")
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
                update_summary_button = ui.button("Update Summary", on_click=partial(
                    update_memory_summary_text, record.id, summary_textarea))
                rerun_summarizer_button = ui.button(
                    "Rerun Summarizer", on_click=partial(rerun_memory_summarizer, record.id))
                delete_button = ui.button("Delete", on_click=partial(delete_memory_text, record.id))
        # await ui.run_javascript(f'window.scrollTo(0, document.body.scrollHeight)', respond=False)
    with chat_container_read:  # use the context of each client to update their ui
        for record in State.instance.LOADED_GAME.messages:
            with ui.card().tight().classes('w-full no-wrap') as card:
                markdown = ui.html(record.text.replace("\n", "<br>")).classes('text-sm m-2')
        # await ui.run_javascript(f'window.scrollTo(0, document.body.scrollHeight)', respond=False)


def update_selected_adapaters():
    log.debug("# update_selected_adapaters...")
    for capability in adapters.AdapterCapability:
        log.debug(f"# get_selected_adapters: {capability.name}")
        State.instance.adapters_ui_data['ui'][capability]['selected'] = get_selected_adapter(
            State.instance.adapters_ui_data['ui'][capability]['selector_ui'])

        log.debug(
            f"# set_settings: {capability.name} > {State.instance.adapters_ui_data['ui'][capability]['selected']}")
        State.instance.adapters_ui_data['ui'][capability]['selected'].set_settings(
            convert_ui_settings(State.instance.adapters_ui_data['ui'][capability]['current_settings']))
    print(State.instance.adapters_ui_data)
    log.debug("# State.instance.LOADED_GAME.summarizer = ...")
    State.instance.LOADED_GAME.summarizer = State.instance.adapters_ui_data[
        'ui'][adapters.AdapterCapability.SUMMARIZATION]['selector_ui'].value
    State.instance.LOADED_GAME.save()

    log.debug("# State.instance.SUM_ADAPTER = ...")
    State.instance.SUM_ADAPTER = State.instance.adapters_ui_data['ui'][adapters.AdapterCapability.SUMMARIZATION]['selected']
    State.instance.TEMPLATE_NAME = textgen_prompt_format.value


async def pg_summarize():
    update_selected_adapaters()
    playground_output.set_value(State.instance.SUM_ADAPTER.summarize(
        playground_input.value).replace("\n", "<br>"))
    
async def pg_generate_character():
    update_selected_adapaters()
    playground_output.set_value(State.instance.adapters_ui_data['ui'][adapters.AdapterCapability.CHARACTER_GENERATOR]['selected'].generate_character())


async def pg_extract_wi(from_input=True):
    update_selected_adapaters()

    auto_world_info_entities = State.instance.adapters_ui_data['ui'][adapters.AdapterCapability.WORLD_INFO_EXTRACTION]['selected'].extract_world_info(playground_input.value if from_input else State.instance.LOADED_GAME.all_text)
    auto_world_info = prompter.entities_to_text(auto_world_info_entities)

    playground_output.set_value(auto_world_info)



# TODO: This should be handled as "Heavy computation" https://github.com/zauberzeug/nicegui/blob/main/examples/progress/main.py
async def send() -> None:
    if State.instance.BUSY:
        log.warning("Server is still busy processing previous request!")
        return
    State.instance.BUSY = True
    State.instance.progress_spinner.visible = True
    final_ai_response = ""
    ai_response = None
    previous_ai_response = None
    message = None
    print()
    log.message("#" * 80)
    update_selected_adapaters()
    for i in range(0, int(paragraphs_to_generate.value)):
        log.message(f"PARAGRAPH {i}...")
        try:
            auto_world_info_entities = State.instance.LOADED_GAME.get_automatic_world_info() if auto_wi_extraction.value is True else None
            prompt = prompter.format_prompt(
                user_prompt=user_prompt.value if i == 0 else user_prompt.value + "\n\n" + final_ai_response,
                summary=State.instance.LOADED_GAME.ai_summary_entries if summary_only_ai_messages.value else State.instance.LOADED_GAME.all_summary_entries,
                world_info=world_info.value,
                auto_world_info_entities=auto_world_info_entities,
                instruction=instruction.value if i == 0 else "Continue your previous response.",
                max_tokens=State.instance.adapters_ui_data['ui'][adapters.AdapterCapability.TEXT_GENERATION]['selected'].get_max_tokens(
                ),
                max_history_tokens=max_history_tokens.value,
                history=State.instance.LOADED_GAME.all_text
            )

            log.message(f"PROMPT: {prompt}")

            if coherence_variations_to_generate.value <= 1:
                ai_response = State.instance.adapters_ui_data['ui'][adapters.AdapterCapability.TEXT_GENERATION]['selected'].generate(
                    prompt)
            else:
                coherence_variants = []
                coherence_scores = []
                for i in range(0, int(coherence_variations_to_generate.value)):
                    variant = State.instance.adapters_ui_data['ui'][adapters.AdapterCapability.TEXT_GENERATION]['selected'].generate(
                        prompt)
                    variant_with_prompt = prompt + variant
                    variant_score = State.instance.adapters_ui_data['ui'][adapters.AdapterCapability.TEXT_COHERENCE_SCORING]['selected'].coherence_score(
                        variant_with_prompt)
                    coherence_variants.append(variant)
                    coherence_scores.append(variant_score)
                # Select text by index of the maximum score varians. If, somehow, 2 variants have the same score it will select the first one it gets.
                # Can be improved upon by selecting a random one, but the change of getting 2 idential float values in real world scenario is very slim
                log.debug("Selection based on scores:")
                log.debug(coherence_scores)
                log.debug(coherence_variants)
                max_number_index = coherence_scores.index(max(coherence_scores))
                log.debug(f"Selection index: {max_number_index}")
                ai_response = coherence_variants[max_number_index]

            log.message("=" * 80)
            log.message(f"RESPONSE: {ai_response}")

            # region Repetition prevention. For now just stopping generation.
            # TODO Improve logic to somehow force it to alter it's result.
            if previous_ai_response is not None and ai_response == previous_ai_response:
                log.warning("Encountered repetition, stopping paragraphs generation.")
                break

            previous_ai_response = ai_response
            # endregion

            if i == 0:
                final_ai_response = ai_response
            else:
                final_ai_response += "\n\n" + ai_response.strip()

        except Exception as e:
            log.error(e, exc_info=True)

    State.instance.LOADED_GAME.add_message(user_prompt.value, "You")
    message = State.instance.LOADED_GAME.add_message(final_ai_response.strip(), "Impish")

    log.message("#" * 80)
    print()
    user_prompt.value = ''
    State.instance.BUSY = False
    State.instance.progress_spinner.visible = False
    notify_sound()
    await reload_chat()
    # await asyncio.gather(*[reload_chat(content) for content in contents])  # run updates concurrently


# region Playground-specific functions
async def pg_load_game_text():
    playground_input.set_value(State.instance.LOADED_GAME.all_text)


async def pg_load_game_summary():
    playground_input.set_value(State.instance.LOADED_GAME.all_summary_entries)

# endregion


# endregion
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
    ui.tab("Playground")

with ui.tab_panels(tabs, value='Read').classes('w-full').style('background-color: rgba(0,0,0,0)'):
    with ui.tab_panel('Read').classes('w-full'):
        chat_container_read = ui.column().classes('w-full max-w-4xl mx-auto')
    with ui.tab_panel('Edit').classes('w-full'):
        chat_container = ui.column().classes('w-full max-w-4xl mx-auto')
    with ui.tab_panel('Playground').classes('w-full'):
        playground_container = ui.column().classes('w-full max-w-4xl mx-auto')
    # ui.button('Choose file', on_click=pick_file).props('icon=folder')

        # update(...) uses run_javascript which is only possible after connecting

    # contents.append(ui.column().classes('w-full max-w-4xl mx-auto'))  # save ui context for updates
    asyncio.run(reload_chat())  # ensure all messages are shown after connecting

State.instance.progress_spinner = ui.spinner()
State.instance.progress_spinner.visible = False
# endregion


# region Drawers
with ui.left_drawer() as left_drawer:
    for adapter_name, adapter_module in adapters.available_adapters.items():
        for capability in adapters.AdapterCapability:
            if capability not in State.instance.adapters_ui_data['ui']:
                State.instance.adapters_ui_data['ui'][capability] = {
                    'adapters': {},
                    'settings_container_ui': None,
                    'selector_ui': None,
                    'ui_update_func': None
                }
            if capability in adapter_module.CAPABILITIES:
                State.instance.adapters_ui_data['ui'][capability]['adapters'][adapter_name] = adapter_module.NAME

    # region Adapters dynamic UI
    async def ui_update(capability) -> None:
        print("UPDATING")
        State.instance.adapters_ui_data['ui'][capability]['settings_container_ui'].clear()
        with State.instance.adapters_ui_data['ui'][capability]['settings_container_ui']:
            State.instance.adapters_ui_data['ui'][capability]['current_settings'] = await adapter_settings_async(get_selected_adapter(State.instance.adapters_ui_data['ui'][capability]['selector_ui']))
        with State.instance.adapters_ui_data['ui'][capability]['selector_ui']:
            docstring = get_selected_adapter(State.instance.adapters_ui_data['ui'][capability]['selector_ui']).__doc__
            ui.tooltip(docstring if docstring else "No description provided for this adapter.")

    for capability in adapters.AdapterCapability:
        State.instance.adapters_ui_data['ui'][capability]['ui_update_func'] = ui_update
        with ui.expansion(f"{adapters.capability_title(capability)}", icon='settings') as expansion_ui:
            State.instance.adapters_ui_data['ui'][capability]['selector_ui'] = ui.select(State.instance.adapters_ui_data['ui'][capability]['adapters'], value=list(State.instance.adapters_ui_data['ui'][capability]['adapters'])[
                0], label=f'{adapters.capability_title(capability)} Adapter', on_change=partial(ui_update, capability))
            with ui.column() as settings_container_ui:
                State.instance.adapters_ui_data['ui'][capability]['settings_container_ui'] = settings_container_ui

                State.instance.adapters_ui_data['ui'][capability]['current_settings'] = adapter_settings(
                    get_selected_adapter(State.instance.adapters_ui_data['ui'][capability]['selector_ui']))

    textgen_prompt_format = ui.select(prompter.get_all_formats(), value=prompter.get_all_formats()[
                                      0], label='TextGen Prompt Format')
    # endregion

    
    tokenizer_name = ui.select(config['tokenizers'], value=list(
        config['tokenizers'])[0], label='Tokenizer', on_change=change_tokenizer)


    summary_only_ai_messages = ui.switch("Include only AI messages in summary", value=False)
    auto_wi_extraction = ui.switch("Perform Auto WI Extraction", value=False)
    paragraphs_to_generate = ui.number("Pargraphs to generate", value=3)
    coherence_variations_to_generate = ui.number("Variations to generate", value=3)

    with ui.row():
        ui.label("Max history tokens:")
        max_history_tokens_label = ui.label("")
    max_history_tokens = ui.slider(value=512, min=0, max=2048).bind_value_to(max_history_tokens_label, "text")

    # export_game_button = ui.button('Export Game', on_click=export_game).props('icon=folder')
    ui.button('Export Game', on_click=export_game).props('icon=folder')

    for capability, adap_data in State.instance.adapters_ui_data['ui'].items():
        log.debug(f"First run, updating UI for: {capability.name}")
        asyncio.run(adap_data['ui_update_func'](capability))
    # asyncio.run(textgen_ui_update())
    # asyncio.run(summarizer_ui_update())

with ui.right_drawer() as right_drawer:
    instruction = ui.textarea("Instruction", value="Continue writing a story")
    world_info = ui.textarea("World Info")

left_drawer.toggle()
right_drawer.toggle()

with playground_container:
    playground_input = ui.textarea("Input:").classes('w-full no-wrap')
    playground_output = ui.textarea("Output:").classes('w-full no-wrap')
    with ui.row():
        ui.button("Summarize", on_click=pg_summarize)
        ui.button("Extract World Info From Input", on_click=partial(pg_extract_wi, True))
        ui.button("Extract World Info From Game", on_click=partial(pg_extract_wi, False))
        ui.button("Generate Character", on_click=pg_generate_character)
        ui.button("Load All Text", on_click=pg_load_game_text)
        ui.button("Load All Summary", on_click=pg_load_game_summary)
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
