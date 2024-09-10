
class CustomLogger:

    LEVELS = {
        0: "DEBUG",
        1: "INFO",
        2: "WARNING",
        3: "ERROR",
        4: "CRITICAL",
    }

    def __init__(self, name, level="INFO"):
        self.name = name
        self.level = level
        self.level_value = self.get_level_value(level)

    def get_level_value(self, level):
        for value, name in self.LEVELS.items():
            if name == level:
                return value
        return 1

    def debug(self, message):
        if self.level_value <= 0:
            print(f"[{self.name}] DEBUG: {message}")

    def info(self, message):
        if self.level_value <= 1:
            print(f"[{self.name}] INFO: {message}")

    def warning(self, message):
        if self.level_value <= 2:
            print(f"[{self.name}] WARNING: {message}")
