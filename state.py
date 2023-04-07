from configuration import config
from utilities.data_utils import sizeof_fmt
import jsonpickle
import os
from paths import DATA_DIR

# region Logger
from debug import get_logger
log = get_logger("default")
# endregion


class State():
    """
    I will burn in hell, but this is a global singleton static variables container,
    used to not deal with proper handling of data passing between NiceGUI
    UI and other stuff.
    """

    def __init__(self) -> None:
        self.BUSY: bool = False
        self.LOADED_GAME = None
        self.TOKENIZER: str = config['tokenizers'][0]
        self.SUM_ADAPTER = None
        self.TEMPLATE_NAME: str = "vicuna"

    def __getstate__(self):
        """
        This allows to alter how jsonpickle handles it.
        """
        state = self.__dict__.copy()

        # This has to be ignored, because otherwise it creates HUGE save data of more than 1.5GB or causes recursion errors
        ignore_vars = ['LOADED_GAME', 'insatnce']
        for dv in ignore_vars:
            if dv in state:
                del state[dv]

        return state

    def __setstate__(self, state):
        ignore_vars = ['LOADED_GAME', 'insatnce']
        for dv in ignore_vars:
            if dv in state:
                del state[dv]

        self.__dict__.update(state)

    def __setattr__(self, name, value) -> None:
        if hasattr(self, "LOADED_GAME") and self.LOADED_GAME is not None:
            log.info("Saving State...")
            state_pickle_bytes = jsonpickle.encode(self).encode("utf-8")
            self.LOADED_GAME.state_pickle = state_pickle_bytes
            self.LOADED_GAME.save()
            log.info(f"State saved, size before compression: {sizeof_fmt(len(state_pickle_bytes))}")
            # with open(os.path.join(DATA_DIR, f"gameuistate_{self.LOADED_GAME.id}.json"), "w+") as f:
            #     f.write(state_pickle)
        return super().__setattr__(name, value)


# This is a singleton
State.instance = State()
