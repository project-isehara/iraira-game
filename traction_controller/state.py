from dataclasses import InitVar, dataclass
from multiprocessing.managers import DictProxy


@dataclass
class AppStateHelper:
    """マルチプロセス時に生で値を触るのがいやなので"""

    _raw: DictProxy

    _running: InitVar[bool]

    def __post_init__(self, _running: bool):
        self._raw["is_running"] = _running

    @property
    def running(self) -> bool:
        return self._raw["is_running"]

    @running.setter
    def running(self, value: bool):
        self._raw["is_running"] = value
