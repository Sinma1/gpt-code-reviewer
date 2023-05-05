from abc import ABC, abstractmethod


class EventHandler(ABC):
    def __init__(self, data):
        self.data = data

    @abstractmethod
    async def handle_event(self):
        pass
