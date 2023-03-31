from nicegui import ui

from configuration import config

# region NiceGUI

#!/usr/bin/env python3
from nicegui import ui

messages = []

@ui.page('/')
def main():
    def send() -> None:
        messages.append(user_prompt.value)
        user_prompt.value = ''

    # anchor_style = r'a:link, a:visited {color: inherit !important; text-decoration: none; font-weight: 500}'
    # ui.add_head_html(f'<style>{anchor_style}</style>')

    content = ui.column().classes('w-full max-w-2xl mx-auto')

    with ui.footer(), ui.column().classes('w-full max-w-3xl mx-auto my-6'):
        with ui.row().classes('w-full no-wrap items-center'):
            user_prompt = ui.input(placeholder='message').props('autofocus input-class=mx-3') \
                .classes('w-full self-center').on('keydown.enter', send)

    async def update_messages() -> None:
        if len(messages) != len(content.default_slot.children):
            content.clear()
            with content:
                for text in messages:
                    ui.markdown(f'{text}').classes('text-lg m-2')
            await ui.run_javascript(f'window.scrollTo(0, document.body.scrollHeight)', respond=False)
    ui.timer(0.1, update_messages)

if config['nicegui']:
    ui.run(**config['nicegui'])
else:
    ui.run()
# endregion
