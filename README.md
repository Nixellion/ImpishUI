# ImpishUI
Storywriting UI with support for KoboldAI and ChatGPT with automatic summarization.

Proof of concept.

## Prerequisites

You need `Python 3` and `pip` installed on your system.

## Installation

1. Clone this repository
2. Create a copy of `config_example.yaml` and rename it to `config.yaml`
3. Check settings available in `config.yaml` and adjust them to your liking
4. On Windows - run `run.bat`. It should `pip install` all the requirements and start the app.
   On Linux or MacOS - run `pip install -r requirements.txt` from withing the current folder, then run `streamlit run app.py`


## Screenshots

![Screenshot](https://media.discordapp.net/attachments/874894021821087745/1090666325870919680/image.png?width=1920&height=837)
![Screenshot](https://media.discordapp.net/attachments/874894021821087745/1090667034041405470/image.png?width=1786&height=905)

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
- [ ] Extra functions and stuff for jinja prompts