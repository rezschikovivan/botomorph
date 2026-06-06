from abc import ABC , abstractmethod
from typing import List
from functools import wraps
import inspect

class FilterMethods():
    """Базовый класс определяющий общьий интерфейс фильтров"""
    @abstractmethod
    def func(self, f:callable)->"Filter": """Фильтр принимающий в качестве параметра функцию и возвращающий объект для обёртывания"""
    @abstractmethod
    def text(self, text)->"Filter":"""Фильтр сравнивающий на полное соответствие текста"""
    @abstractmethod
    def in_text(self, text)->"Filter":"""Фильтр проверяет наличие подстроки в тексте сообщения"""
    @abstractmethod
    def cmnd(self, text)->"Filter":"""Фильтр реагирует на сообщени команды начинающееся с '/'"""
    @abstractmethod
    def photo(self)->"Filter":"""Фильтр реагирует когда присылают сообщение-фото"""
    @abstractmethod
    def video(self)->"Filter":"""Фильтр реагирует когда присылают сообщение-видео"""
    @abstractmethod
    def audio(self)->"Filter":"""Фильтр реагирует когда присылают сообщение-аудио"""
    @abstractmethod
    def document(self)->"Filter":"""Фильтр реагирует когда присылают сообщение-документ"""
    @abstractmethod
    def location(self)->"Filter":"""Фильтр реагирует когда присылают сообщение-локацию"""
    @abstractmethod
    def voice(self)->"Filter":"""Фильтр реагирует когда присылают сообщение-голос"""
    @abstractmethod
    def sticker(self)->"Filter":"""Фильтр реагирует когда присылают стикер"""

class Filter(FilterMethods):
    """Класс посредник предоставляет доступ к представлению фильтра. Конкретная реализация (подкласс ABCFilter)
    определяется на этапе регистрации класса-хэндлера в ядре от компонента"""
    __implementation:"BaseFilterImplementor" = None
    __filter_methods:List = [i for i in FilterMethods.__dict__.keys() if not i.startswith("_")]

    def __init__(self):
        self.filters = []

    def __getattribute__(self, name):
        if name !='_Filter__filter_methods' and name in self.__filter_methods:
            def wrapper(func):
                @wraps(func)
                def wrap(*args):
                    if len(args) != len(inspect.signature(func).parameters.values()): raise TypeError(f"Передано неверное количество аргументов в метод {func.__name__}")
                    self.filters.append([func.__name__, *args])
                    return self
                return wrap
            return wrapper(super().__getattribute__(name))
        return super().__getattribute__(name)

    @property
    def filter_imp(self):return self.__implementation
    @filter_imp.setter
    def filter_imp(self, new): self.__implementation = new

    def ivoke_imp(self)-> List[callable] | None:
        """Возвращает фильтры полученные от компонента, используя полиморфную связь через базовый FilterMethods"""
        if self.filter_imp is None: return None
        final_filters = []
        for f in self.filters:
            final_filters.append(self.filter_imp.__getattribute__(f[0])(*f[1:]))
        return final_filters

class BaseFilterImplementor(FilterMethods, ABC):
    """Методы наследников этого класса должны переопределять методы-фильтры для возвращения фильтрующего обьекта соответствующей библиотеки"""
    @abstractmethod
    def func(self, f):pass
    def text(self, text:str): return self.func(lambda x : x.text.lower() == text.lower())
    def in_text(self, text): return self.func(lambda x : text.lower() in x.text.lower())
    def cmnd(self, text): return self.func(lambda x : x.text.lower() == f"/{text}".lower())
