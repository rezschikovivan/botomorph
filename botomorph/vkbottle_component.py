from botomorph.core import BaseComponent, BaseFilterImplementor
from botomorph.message import BaseMsg,Button,Sender
from botomorph.message import Keyboard
from typing import Dict, Any
import asyncio
from vkbottle.dispatch.rules.base import AttachmentTypeRule, PayloadRule
from vkbottle.dispatch.handlers import FromFuncHandler
from vkbottle.dispatch.rules import ABCRule
from vkbottle.bot import Message, Bot
from vkbottle import Keyboard, OpenLink, Callback, Text
from vkbottle_types.objects import UsersUserFull

class VKFilter(BaseFilterImplementor):
    """Реализует работу с фильтрами vkbottle"""
    def func(self, f):
        class CustomRule(ABCRule[Message]):
            def __init__(self, *func: callable):
                self.func = func

            async def check(self, event: Message)->bool:
                for f in self.func:
                    if f(event): continue
                    return False
                else: return True
        return CustomRule(f)
    def callback(self, data):
        return super().callback(data)
    def photo(self):
        return AttachmentTypeRule("photo")
    def video(self):
        return AttachmentTypeRule("video")
    def audio(self):
        return AttachmentTypeRule("audio")
    def document(self):
        return AttachmentTypeRule("doc")
    def location(self):
        return AttachmentTypeRule("geo")
    def voice(self):
        return AttachmentTypeRule("voice")
    def sticker(self):
        return AttachmentTypeRule("sticker")
    
class VKMsger(BaseMsg):
    """Реализует взаимодействие спользователем вк (отправка сообщений и тп)"""
    msg:Message# нужно чтобы интерпритатор видел тип поля
    def __init__(self, msg):
        super().__init__(msg)
    @classmethod
    def msg_type(cls):
        return Message
    async def answer(self, text):
        return await self.msg.answer(text)
    async def delete(self):
        raise RuntimeError("VKBottleComponent пока не умеет удалять сообщения (я не нашел)")
    async def reply(self, text):
        await self.msg.reply(text)
    async def send_reply_kboard(self, keyboard:Keyboard, text:str|None = None):
        vk_keyboard:Keyboard = Keyboard(True, False)
        self.create_vk_kboard(vk_keyboard, keyboard)
        await self.msg.answer(text, keyboard=vk_keyboard)
    async def send_inline_kboard(self, keyboard:Keyboard, text:str|None = None):
        vk_keyboard:Keyboard = Keyboard(False, True)
        self.create_vk_kboard(vk_keyboard, keyboard)
        await self.msg.answer(text, keyboard=vk_keyboard)
    def create_vk_kboard(self, vk_keyboard:Keyboard, keyboard:Keyboard):
        row = 0
        for b in keyboard.buttons:
            if b.row == row:
                self.add_button(vk_keyboard, b)
            else:
                row = b.row
                vk_keyboard.row()
                self.add_button(vk_keyboard, b)
    def add_button(self, vk_keyboard:Keyboard, button:Button):
        if button.is_url:
            vk_keyboard.add(OpenLink(button.action, button.text))
        elif button.is_callback:
            vk_keyboard.add(Callback(button.text, {"payload":list(button.action.values())[0]}))
        else: 
            vk_keyboard.add(Text(button.text, payload={"payload":str(button.action)}))
    @property
    def date(self):
        return self.msg.date
    @property
    def text(self):
        return self.msg.text
    @property
    def document(self):
        return self.msg.get_doc_attachments()
    @property
    def audio(self):
        return self.msg.get_audio_attachments()
    @property
    def video(self):
        return self.msg.get_video_attachments()
    @property
    def location(self):
        raise RuntimeError("VKBottleComponent пока не умеет (я не нашел)")
    @property
    def voice(self):
        return self.msg.get_audio_message_attachments()
    @property
    def photo(self):
        return self.msg.get_photo_attachments()
    @property
    async def sender(self):
        user: UsersUserFull = await self.msg.get_user()
        return Sender(user.id, user.first_name, user.last_name, user.nickname)
    @property
    async def get_seder(self):
        user = await self.msg.get_user()
        return Sender(user.id, user.first_name, user.last_name, user.nickname)

class VKBottleComponent(BaseComponent):
    """Базовый компонент указывающий что класс-хэндлер относится к компоненту VKBottleComponent"""
    bots:Dict[str, Bot] = {}
    @classmethod
    def get_filter(cls):
        return VKFilter
    @classmethod
    def get_messager(cls):
        return VKMsger
    @classmethod
    def add_bot(cls, token:str):
        if not token in cls.bots.keys():
            cls.bots[token] = Bot(token=token)
    @classmethod
    def register_handler(cls, token, method, *filters):
        if filters is None:
            return cls.bots[token].labeler.message_view.handlers.append(FromFuncHandler(method))
        cls.bots[token].labeler.message_view.handlers.append(FromFuncHandler(method, *filters))
    @classmethod
    def cretae_polling_tasks(cls):
        tasks = []
        for bot in cls.bots.values():
            tasks.append(cls.__castom_polling(bot))
        return tasks
    
    async def __castom_polling(bot:Bot, sleep_time:float=0.01):
        while True:
            async for event in bot.polling.listen():
                for update in event.get("updates"):
                    await bot.router.route(update, bot.polling.api)
            await asyncio.sleep(sleep_time)