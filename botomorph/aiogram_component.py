import asyncio
from botomorph.core import BaseComponent, BaseFilterImplementor, BaseMsg
from botomorph.message import BaseMsg, Sender, Keyboard
from typing import Dict
from aiogram.types import Message, KeyboardButton, InlineKeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup
from aiogram.filters import BaseFilter
from aiogram import Bot, Dispatcher

#компонент должен реализовать абстрактный класс, проверить с помощю: AiogramFilter()
class AiogramFilter(BaseFilterImplementor):
    
    def func(self, f: callable):
        class CustomFilter(BaseFilter):
            def __init__(self, *func: callable):
                self.func = func

            # ИСПРАВЛЕНО: async def вместо def
            async def __call__(self, event) -> bool:
                for f in self.func:
                    # ИСПРАВЛЕНО: проверка на корутину
                    if asyncio.iscoroutinefunction(f):
                        result = await f(event)
                    else:
                        result = f(event)
                    
                    if not result:
                        return False
                return True
        return CustomFilter(f)
    
    def photo(self):
        async def check_photo(message: Message) -> bool:
            return bool(message.photo)
        # ИСПРАВЛЕНО: возвращаем экземпляр фильтра
        return self.func(check_photo)

    def video(self):
        async def check_video(message: Message) -> bool:
            return bool(message.video)
        return self.func(check_video)

    def audio(self):
        async def check_audio(message: Message) -> bool:
            return bool(message.audio)
        return self.func(check_audio)

    def document(self):
        async def check_document(message: Message) -> bool:
            return bool(message.document)
        return self.func(check_document)

    def location(self):
        async def check_location(message: Message) -> bool:
            return bool(message.location)
        return self.func(check_location)

    def voice(self):
        async def check_voice(message: Message) -> bool:
            return bool(message.voice)
        return self.func(check_voice)

    def sticker(self):
        async def check_sticker(message: Message) -> bool:
            return bool(message.sticker)
        return self.func(check_sticker)
#компонент должен реализовать абстрактный класс, проверить с помощю: AiogramMsg()
class AiogramMsg(BaseMsg):
    
    msg:Message

    def __init__(self, msg: Message):
        super().__init__(msg)
    @classmethod
    def msg_type(cls):
        return Message
    async def answer(self, text):
        return await self.msg.answer(text)
    
    async def reply(self, text):
        return await self.msg.reply(text)
    
    async def delete(self):
        return await self.msg.delete()
    
    async def send_reply_kboard(self, keyboard: Keyboard, text: str | None = None):
        reply_markup = self._create_reply_keyboard(keyboard)
        await self.msg.answer(
            text, 
            reply_markup=reply_markup
        )

    async def send_inline_kboard(self, keyboard: Keyboard, text: str | None = None):
        inline_markup = self._create_inline_keyboard(keyboard)
        await self.msg.answer(
            text, 
            reply_markup=inline_markup
    )


    def _create_reply_keyboard(self, keyboard: Keyboard) -> ReplyKeyboardMarkup:
        """Создаёт ReplyKeyboardMarkup из объекта Keyboard"""
        rows = self._build_button_rows(keyboard, is_inline=False)
    
        return ReplyKeyboardMarkup(
            keyboard=rows,
            resize_keyboard=True,
            one_time_keyboard=False
        )

    def _create_inline_keyboard(self, keyboard: Keyboard) -> InlineKeyboardMarkup:
        """Создаёт InlineKeyboardMarkup из объекта Keyboard"""
        rows = self._build_button_rows(keyboard, is_inline=True)
    
        return InlineKeyboardMarkup(inline_keyboard=rows)

    def _build_button_rows(self, keyboard: Keyboard, is_inline: bool):
        """Внутренний метод для построения рядов кнопок"""
        
        rows = []
        current_row = []
        current_row_index = 0
        
        for button in keyboard.buttons:
            if button.row != current_row_index:
                if current_row:
                    rows.append(current_row)
                current_row = []
                current_row_index = button.row
            
            if is_inline:
                # Inline кнопка
                if button.is_url:
                    btn = InlineKeyboardButton(text=button.text, url=button.action)
                elif button.is_callback:
                    callback_value = list(button.action.values())[0] if isinstance(button.action, dict) else button.action
                    btn = InlineKeyboardButton(text=button.text, callback_data=str(callback_value))
                else:
                    btn = InlineKeyboardButton(text=button.text, callback_data=str(button.action) if button.action else button.text)
            else:
                # Reply кнопка
                btn = KeyboardButton(text=button.text)
            
            current_row.append(btn)
        
        if current_row:
            rows.append(current_row)
        return rows


    @property
    def date(self):
        return self.msg.date
    
    @property
    def text(self):
        return self.msg.text or ""
    
    @property
    def photo(self):
        return self.msg.photo[-1] if self.msg.photo else None
    
    @property
    def document(self):
        return self.msg.document
    
    @property
    def audio(self):
        return self.msg.audio
    
    @property
    def video(self):
        return self.msg.video
    
    @property
    def location(self):
        return self.msg.location
    
    @property
    def voice(self):
        return self.msg.voice
    
    @property
    async def sender(self):
        user = self.msg.from_user
        if user:
            return Sender(user.id, user.first_name, user.last_name, user.username)
        return None

#компонент должен реализовать абстрактный класс
class AiogramComponent(BaseComponent):
    bots: Dict[str,Bot] = {}
    dispatchers: Dict[str,Dispatcher] = {}
    @classmethod
    def get_filter(cls):
        return AiogramFilter
    @classmethod
    def get_messager(cls):
        return AiogramMsg
    @classmethod
    def add_bot(cls, token:str):
        if  token not in cls.bots.keys():
            cls.bots[token] = Bot(token=token)
            cls.dispatchers[token] = Dispatcher()
    @classmethod
    def register_handler(cls, token, method, *filters):
        cls.dispatchers[token].message.register(method, *filters)
    @classmethod
    def cretae_polling_tasks(cls):
        tasks = []
        for token, disp in cls.dispatchers.items():
            tasks.append(disp.start_polling(cls.bots[token]))
        return tasks