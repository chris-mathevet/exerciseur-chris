import traceback

class ErreurVoilée(Exception):
    def __init__(self, exc_type, exc_value, exc_traceback):
        self.e_type = exc_type
        self.e_interne = exc_value
        self.e_tb = traceback.format_tb(exc_traceback)
        if len(self.e_tb) > 1:
            self.e_tb = self.e_tb[1:]

    def messages(self):
        return self.e_tb

class VoilePudique:
    def __init__(self, fonction_raise):
        self.fonction_raise = fonction_raise

    def __enter__(self):
        pass

    def __exit__(self, e_type, e_value, e_traceback):
        if e_type:
            if isinstance(e_value, ErreurVoilée):
                raise e_value
            else:
                raise self.fonction_raise(e_type, e_value, e_traceback)
