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
4. On Windows - run `install_requirements.bat` first, and then run `run.bat`. You may need to run `install_requirements.bat` after every git pull just to make sure everything is up to date.
   On Linux or MacOS - run `pip install -r requirements.txt` from within the current folder, then run `python3 app.py` for older systems or `python app.py` for newer, but if you're on linux you probably know :)


## Troubleshooting

If you get an error about missing `en_core_web_sm`, that means that for some reason install_requirements.bat didn't download it. 
Depending on your python installation environment you may need to adjust this command and run it manually: `python -m spacy download en_core_web_sm`



## Screenshots

![Screenshot](https://i.imgur.com/vbIfILv.png)
![Screenshot](https://i.imgur.com/EiSSnoI.png)


## Configuration

Section is under WIP. 

Check "prompt_templates" folder and jinja2 documentation to learn about how to add new prompts. Just create a new file with jinja2 extension and write your own prompt format.

Pull requests with custom adapters and prompt formats are also welcome.
