# Class: CS 476
# Professor: Dr. Samira Sadaoui
# filename: obsever.py
# Purpose: Code for observer pattern

from abc import ABC, abstractmethod
from typing import List
from ..models import Tournament

class Observer(ABC):
    @abstractmethod
    def update(self, tournament: Tournament, message: str) -> None:
        pass

class Subject(ABC):
    def __init__(self) -> None:
        self._observers: List[Observer] = []

    @abstractmethod
    def attach(self, observer: Observer) -> None:
        pass

    @abstractmethod
    def detach(self, observer: Observer) -> None:
        pass

    @abstractmethod
    def notify(self, tournament: Tournament, message: str) -> None:
        pass