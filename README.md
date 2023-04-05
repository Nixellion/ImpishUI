# ImpishUI
Writing UI with support for KoboldAI and ChatGPT with automatic summarization.

## Features

- Automatic summarization that strifes to keep as much important information as it can within LLM context token limits
- Adapter system that allows easily writing new text generation and summarization "plugins"
- Included text generation adapters: KoboldAI, OpenAI
- Included summarization adapters: KoboldAI, OpenAI, Sumy (fast)
- Flexible prompt templating with Jinja2
- SQLite database keeping your logs and all the important information
- Export your chat\story logs to files
- And more coming

## Prerequisites

You need `Python 3` and `pip` installed on your system.

## Installation

1. Clone this repository
2. Create a copy of `config_example.yaml` and rename it to `config.yaml`
3. Check settings available in `config.yaml` and adjust them to your liking
4. On Windows - run `run.bat`. It should `pip install` all the requirements and start the app.
   On Linux or MacOS - run `pip install -r requirements.txt` from withing the current folder, then run `streamlit run app.py`


## Screenshots

![Screenshot](https://i.imgur.com/vbIfILv.png)
![Screenshot](https://i.imgur.com/EiSSnoI.png)


## Configuration

Section is under WIP. 

Check "prompt_templates" folder and jinja2 documentation to learn about how to add new prompts. Just create a new file with jinja2 extension and write your own prompt format.

Pull requests with custom adapters and prompt formats are also welcome.

## TODO

- [x] Add World Info field that will be persistent throughout the story always prepended.
- [x] Token length checks to dynamically expand and contract the prompt to fit the specified length
- [x] openai_requester.py cleanup
- [x] Improve responsiveness and formatting https://github.com/kinosal/tweet/blob/main/app.py
- [x] Add "Edit" checkbox to edit text in place
- [x] Cleanup code, check and upload
- [x] Create an alternate mode in which it summarizes stories in parts
- [x] Savegames
- [ ] "Processing" state, locking UI and showing progress spinner or bar
- [ ] Savegames UI, selecting and adding games
- [ ] Remember settings
- [ ] Reading and Editing modes
- [ ] Story export options
- [ ] ...