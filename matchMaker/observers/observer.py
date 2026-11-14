# Class: CS 476
# Professor: Dr. Samira Sadaoui
# filename: obsever.py
# Purpose: Code for observer pattern

from abc import ABC, abstractmethod

class Observer(ABC):
    @abstractmethod
    def update(self, tournament, message):
        pass

class Subject(ABC):
    @abstractmethod
    def attach(self, observer: Observer):
        pass

    @abstractmethod
    def detach(self, observer: Observer):
        pass

    @abstractmethod
    def notify(self, tournament, message):
        pass