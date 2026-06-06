from botomorph.handle import Handler
from botomorph.filter import BaseFilterImplementor
from typing import List,Dict, Coroutine,Any,  Set, Tuple
from botomorph.message import BaseMsg, MsgFactory
from abc import ABCMeta, abstractmethod
import asyncio
    
class ClsComponenter():
    """Класс реализующий работу по инициализации классов-компонентов"""
    def before(cls, mcs, name, bases, attrs): 
        """Вызывается перед регистрацией компонента"""

    def registrate_cmpnt(cls ,mcs, name, bases, attrs)-> Tuple["CoreMeta", str, Tuple[object], Dict[str,object]]:
        """Регистрирует компонент"""
        return (mcs, name, bases, attrs)

    def after(cls, new_cls:"BaseComponent", mcs, name, bases, attrs): 
        """Вызывается после регистрации и проверки имплементации абстрактных методов компонента. Выполняет регистрацию компонена в фабрике сообщений messaging.MsgerFactory"""
        MsgFactory.registr_component(new_cls.get_messager())
        if new_cls.get_messager() is None: print(f"Warning! {name}.get_messager() not returns ABCMessager. The functionality of sending messages and related features will be unavailable.")
        if new_cls.get_filter() is None: print(f"Warning! {name}.get_filter() not returns ABCFilter. The functionality of filtering messages and related features will be unavailable.")
        return (mcs, name, bases, attrs)
class ClsHandler():
    """Класс реализующий работу по инициализации классов-хэндлеров"""
    base_cmpnts:Set["BaseComponent"] = set()

    def before(cls, mcs, name, bases, attrs):
        """Вызывается перед регистрацией класса-хендлера""" 
    
    def registrate_handler(self, mcs, name:str, bases: Tuple[object], attrs:Dict[str,Any])-> Tuple["CoreMeta", str, Tuple[object], Dict[str,object]]:
        """Регистрирует хэндлер"""
        # находим компонент этого класса
        base_cmpnt: BaseComponent = self.__get_parent_basecmpnt_subclass(bases, name)
        bases_plenty: List[Dict] = list(bases)
        self.base_cmpnts.add(bases_plenty[bases_plenty.index(base_cmpnt)])

        #составляем аттрибуты класса в одном cловаре с родительсими
        all_attrs:Dict = self.__get_all_attrs(bases_plenty, attrs)

        # ищем токен
        token = all_attrs.get("TOKEN")
        if token is None: raise ValueError(f"Необходимо указать значение переменной класса: TOKEN в {name}")
        base_cmpnt.add_bot(token)

        # регистриуем хэндлеры с фильтрами 
        for i in all_attrs.values():
            if isinstance(i, Handler):
                fltrs = []
                for filter in i.filters:
                    if base_cmpnt.get_filter() is None: break
                    filter.filter_imp = base_cmpnt.get_filter()() if isinstance(base_cmpnt.get_filter()(), BaseFilterImplementor) else None
                    if filter.filter_imp is None: break
                    fltrs.extend(filter.ivoke_imp())
                base_cmpnt.register_handler(token, i, *fltrs)
        return (mcs, name, bases, all_attrs)

    def after(self, new_cls, mcs, name, bases, attrs:Dict[str,Any]):
        """Вызывается после регистрации и проверки на реализации абстрактных методов класса-хэндлера""" 
        for attr in attrs.values():
            if isinstance(attr, Handler):
                attr.func_cls = new_cls
        return (mcs, name, bases, attrs)

    async def activate_pollings(self):
        """ Запускает поллинг для всех классов-хэндлеров"""
        corouts = list()
        for b in self.base_cmpnts:
            tasks = b.cretae_polling_tasks()
            for task in tasks:
                corouts.append(task)
        return await asyncio.gather(*corouts)
    
    def __get_all_attrs(self, bases: Tuple[Any], attrs:Dict[str,Any])->Dict[str,Any]:
        """возвращает общий словарь с атрибутами класса и его родителей"""
        all_attrs:Dict = dict()
        for c in bases:
            for n, a in c.__dict__.items():
                if not n.startswith("_"):
                    all_attrs[n] = a
            
        for n, a in attrs.items():
            if not n.startswith("_"):
                all_attrs[n] = a
        return all_attrs
    def __get_parent_basecmpnt_subclass(self, bases: Tuple[object], name:str = "НЕ_УКАЗАН")->"BaseComponent":
        """Ищет в кортеже классов-родителей подкласс BaseComponent"""
        base_cmpnt = None
        for b in bases:
            if issubclass(b,BaseComponent):# если b подкласс BaseComponent, то значит все правильно
                if base_cmpnt is not None: 
                    print(f"Warning! The class {name} has several parents from the BaseComponent. Only the first one will be used.")
                    break
                base_cmpnt = b
        if base_cmpnt is None: raise BaseException(f"Класс-хэндлер {name} необходимо наследовать от компонента реализующего BaseComponent")# если меткласс указали напрямую 
        return base_cmpnt

class CoreMeta(ABCMeta):
    """Метакласс для классов-хэндлеров и классов-компонентов. Региулирует их создание и взаимодействие. Напрямую не использовать"""
    __cls_component = ClsComponenter()   # класс для добваления классов интегрирующих работу с API
    __cls_handler = ClsHandler()         # класс для добавления классов-хэндлеров

    def __new__(mcs, name:str, bases, attrs:Dict[str,Any]):
        if name == "BaseComponent":
            return super().__new__(mcs, name, bases, attrs)
        elif BaseComponent in bases: 
            return super().__new__(*mcs.__generate_component(name, bases, attrs))
        else: 
            return super().__new__(*mcs.__generate_handler(name, bases, attrs))
    @classmethod
    def __generate_handler(mcs, name, bases, attrs):
        """Выполняет ряд операций по созданию компонента"""
        mcs.__cls_handler.before(mcs, name, bases, attrs)
        new_values = mcs.__cls_handler.registrate_handler(mcs, name, bases, attrs)
        cls = super().__new__(*new_values)
        cls()
        new_values = mcs.__cls_handler.after(cls, *new_values)
        return new_values
    @classmethod
    def __generate_component(mcs, name, bases, attrs):
        """Выполняет ряд операций по созданию клс-хэндлера"""
        mcs.__cls_component.before(mcs, name, bases, attrs)
        new_values = mcs.__cls_component.registrate_cmpnt(mcs, name, bases, attrs)
        cls = super().__new__(*new_values)
        cls()
        new_values = mcs.__cls_component.after(cls, *new_values)
        return new_values
    @classmethod
    def set_cls_componenter(cls, new_registrator: ClsComponenter):
        """Заменяет класс для работы с компонентами внутри ядра"""
        if issubclass(new_registrator, ClsComponenter):
            cls.__cls_component = new_registrator
        else: raise TypeError("Должен быть субкалссом: ClsRegistrator")
    @classmethod
    def set_cls_handler(cls, new_registrator: ClsHandler):
        """Заменяет класс для работы с классами-хэндлерами внутри ядра"""
        if issubclass(new_registrator.__class__, ClsHandler):
            cls.__cls_handler = new_registrator
        else: raise TypeError("Должен быть субкалссом: ClsHandler")
    @classmethod
    def get_cls_handler(cls)-> ClsHandler:
        """Возвращет текущий класс для работы с классами-хэндлерами внутри ядра"""
        return cls.__cls_handler
    @classmethod
    def get_cls_componenter(cls)-> ClsComponenter:
        """Возвращает текущий класс для работы с компонентами внутри ядра"""
        return cls.__cls_component
    
def start_bots():
    """Запускает асинхронный цикл соытий для поллинга всех классов-хэндлеров"""
    return CoreMeta.get_cls_handler().activate_pollings()

def set_cmpnts_registrator(new_registrator: ClsComponenter):
    """Заменяет класс для работы с компонентами внутри ядра"""
    CoreMeta.set_cls_componenter(new_registrator)

def set_handlers_registrator(new_registrator:ClsHandler):
    """Заменяет класс для работы с классами-хэндлерами внутри ядра"""
    CoreMeta.set_cls_handler(new_registrator)

# Базовый класс для компонентов
class BaseComponent(metaclass=CoreMeta):
    """ Базовый класс для компонентов"""
    bots = {}
    
    @classmethod
    @abstractmethod
    def get_filter(cls)-> BaseFilterImplementor|None:
        """Возвращает реализованный подкласс ABCFilter."""
    @classmethod
    @abstractmethod
    def get_messager(cls)-> BaseMsg|None:
        """Возвращает реализованный подкласс ABCMsger."""
    @classmethod
    @abstractmethod
    def add_bot(cls, token:str):
        """ Добавляет экземпляр бота в поле класса bots:Dict[token:botinstance], если такого токена еще не было. """
    @classmethod
    @abstractmethod
    def register_handler(cls, token, method, *filters):
        """ Регистрирует переданный метод как обработчик в боте под указанным токеном. """
    @classmethod
    @abstractmethod
    def cretae_polling_tasks(cls)->Coroutine:
        """ Возвращает корутину для опроса сервера (поллинга) всех ботов."""