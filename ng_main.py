#!/usr/bin/env python3



import asyncio
from nicegui import ui, Client
from ng_local_file_picker import local_file_picker
from ng_adapter_settings import adapter_settings
import adapters
import prompter
from database import Game, Settings, Message, Character, State
from functools import partial

# region Logger
import os
from debug import get_logger
log = get_logger(os.path.basename(os.path.realpath(__file__)))
# endregion


async def pick_file() -> None:
    result = await local_file_picker('~', multiple=True)
    ui.notify(f'You chose {result}')

# contents = []
# chat_container = None
State.load_game(1)

# TODO The fuck not working here


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
    # Yeah, NiceGUI while nice has it's quirks, like heavy context dependence, and so far I didn't find a way to move these functinos outside of this route function. But it works and looks fine for now.
    async def update_memory_text(message_id, textarea) -> None:
        log.info(f"Updating message {message_id}.")
        message = Message.select().where(Message.id == message_id).get()
        message.text = textarea.value
        message.save()
        await reload_chat()
        
    async def change_tokenizer() -> None:
        State.TOKENIZER = tokenizer_name.value

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
            for record in State.LOADED_GAME.messages:
                with ui.card().tight().classes('w-full no-wrap') as card:
                    textarea = ui.textarea(record.author, value=record.text).classes('text-sm m-2')
                    update_button = ui.button("Update", on_click=partial(update_memory_text, record.id, textarea))
                    delete_button = ui.button("Delete", on_click=partial(delete_memory_text, record.id))
            # await ui.run_javascript(f'window.scrollTo(0, document.body.scrollHeight)', respond=False)
        with chat_container_read:  # use the context of each client to update their ui
            for record in State.LOADED_GAME.messages:
                with ui.card().tight().classes('w-full no-wrap') as card:
                    markdown = ui.markdown(record.text).classes('text-sm m-2')
            # await ui.run_javascript(f'window.scrollTo(0, document.body.scrollHeight)', respond=False)

    async def send() -> None:
        chosen_textgen_adapter = get_selected_adapter(textgen_adapter)
        chosen_sum_adapter = get_selected_adapter(summarizer_adapter)

        chosen_textgen_adapter.set_settings(convert_ui_settings(textgen_settings))
        chosen_sum_adapter.set_settings(convert_ui_settings(summarizer_settings))

        State.LOADED_GAME.summarizer = summarizer_adapter.value
        State.LOADED_GAME.save()

        State.LOADED_GAME.add_message(user_prompt.value, "You")

        State.SUM_ADAPTER = chosen_sum_adapter
        State.TEMPLATE_NAME = textgen_prompt_format.value

        prompt = prompter.format_prompt(
            user_prompt=user_prompt.value,
            summary=State.LOADED_GAME.all_summary_entries,
            world_info=None,
            instruction=None,
            max_tokens=chosen_textgen_adapter.get_max_tokens()
            )

        ai_response = chosen_textgen_adapter.generate(prompt)
        State.LOADED_GAME.add_message(ai_response, "Impish")

        user_prompt.value = ''
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
    await client.connected()
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
    await reload_chat()  # ensure all messages are shown after connecting
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

        async def textgen_ui_update() -> None:
            textgen_ui.clear()
            with textgen_ui:
                textgen_settings = adapter_settings(get_selected_adapter(textgen_adapter))
            with textgen_adapter:
                docstring = get_selected_adapter(textgen_adapter).__doc__
                ui.tooltip(docstring if docstring else "No description provided for this adapter.")

        textgen_adapter = ui.select(text_generation_adapters, value=list(summarization_adapters)[
                                    0], label='TextGen Adapter', on_change=textgen_ui_update)
        with ui.expansion(f"Textgen settings", icon='gear') as textgen_ui:
            textgen_settings = adapter_settings(get_selected_adapter(textgen_adapter))

        textgen_prompt_format = ui.select(prompter.get_all_formats(), value=prompter.get_all_formats()[0], label='TextGen Prompt Format')

        async def summarizer_ui_update() -> None:
            summarizer_ui.clear()
            with summarizer_ui:
                summarizer_settings = adapter_settings(get_selected_adapter(summarizer_adapter))
            with summarizer_adapter:
                docstring = get_selected_adapter(summarizer_adapter).__doc__
                ui.tooltip(docstring if docstring else "No description provided for this adapter.")

        summarizer_adapter = ui.select(summarization_adapters, value=list(
            summarization_adapters)[0], label='Summarization Adapter', on_change=summarizer_ui_update)
        
        with ui.expansion(f"Summarizer settings", icon='gear') as summarizer_ui:
            summarizer_settings = adapter_settings(get_selected_adapter(summarizer_adapter))

        tokenizer_name = ui.select(config['tokenizers'], value=list(
            config['tokenizers'])[0], label='Tokenizer', on_change=change_tokenizer)
        
        await textgen_ui_update()
        await summarizer_ui_update()

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


from configuration import config
if config['nicegui']:
    ui.run(**config['nicegui'])
else:
    ui.run()
