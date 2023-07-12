import subprocess
from abc import abstractmethod, ABC

from .morpheme import Morpheme


class AbstractController(ABC):
    @abstractmethod
    def spawn_mecab(self) -> None:
        pass

    @abstractmethod
    def dispose_mecab(self) -> None:
        pass

    @abstractmethod
    def get_morphemes(self, expression: str) -> list[Morpheme]:
        pass

    @abstractmethod
    def get_description(self) -> str:
        """
        Returns a single line, for which languages this Morphemizer is.
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass
