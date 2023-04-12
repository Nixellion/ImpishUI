from configuration import config
from utilities.data_utils import sizeof_fmt
import jsonpickle
import os
from paths import DATA_DIR

# region Logger
from debug import get_logger
log = get_logger("default")
# endregion

from pprint import PrettyPrinter

pp = PrettyPrinter()


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
        self.adapters_ui_data = {'ui': {},
                                 'settings': {}}

    def __getstate__(self):
        """
        This allows to alter how jsonpickle handles it.
        """
        state = self.__dict__.copy()

        # This has to be ignored, because otherwise it creates HUGE save data of more than 1.5GB or causes recursion errors
        ignore_vars = ['LOADED_GAME', 'instance']
        for dv in ignore_vars:
            if dv in state:
                del state[dv]

        return state

    def __setstate__(self, state):
        try:
            ignore_vars = ['LOADED_GAME', 'instance']
            for dv in ignore_vars:
                if dv in state:
                    del state[dv]

            self.__dict__.update(state)
        except Exception as e:
            log.critical(f"Failed restoring state! {e}")

    def __setattr__(self, name, value) -> None:
        # if name == "adapters_ui_data":
        #     pp.pprint(value)
        if hasattr(self, "LOADED_GAME") and self.LOADED_GAME is not None:
            log.info("Saving State...")
            try:
                log.warning("State saving is disabled due to a bug in the code. All blame on developer, this is a known issue I'm working on. As a user you can ignore this warning.")
                # state_pickle_bytes = jsonpickle.encode(self).encode("utf-8")
                # self.LOADED_GAME.state_pickle = state_pickle_bytes # BUG Disabling until bug fixed
                # self.LOADED_GAME.save()
                # log.info(f"State saved, size before compression: {sizeof_fmt(len(state_pickle_bytes))}")
            except Exception as e:
                log.critical(f"Failed saving state! {e}")
            # with open(os.path.join(DATA_DIR, f"gameuistate_{self.LOADED_GAME.id}.json"), "w+") as f:
            #     f.write(state_pickle)
        return super().__setattr__(name, value)

    def __getattribute__(self, __name: str):
        value = super().__getattribute__(__name)
        # if __name == "adapters_ui_data":
        #     pp.pprint(value)
        return value
# This is a singleton
State.instance = State()
