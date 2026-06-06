import time

t1 = time.time()

from botomorph import Filter, Handler, BaseMsg, Sender, BaseComponent, Keyboard, start_bots
#from abot.aiogram_component import AiogramComponent
from botomorph.vkbottle_component import VKBottleComponent
from botomorph.aiogram_component import AiogramComponent

t2 = time.time()
print(t2-t1)

import tokens

vk_token = tokens.vk_token
tgram_token = tokens.tgram_token

# ПРИМЕР ИСПОЛЬЗОВАНИЯ. ТЕСТОВ ПОКА НЕТ...

# class F(ClsHandler, ABC):
#     @classmethod
#     def before(cls, mcs, name, bases, attrs):
#         if attrs.get("updates") is None: raise AttributeError(f"релизуйте метод updates в {name}")
#         attrs["updates"] = classmethod(attrs["updates"])
#     @classmethod
#     def after(cls, new_cls:Observer, mcs, name, bases, attrs):
#         new_cls.register_as_observer()

# set_handlers_registrator(F)

class Echo():

    @Handler(Filter().in_text("name2"))
    async def cab8(cls, message:BaseMsg):
        await message.answer(message, "Вы воспользовались кнопкой!")

class VKEcho(Echo, VKBottleComponent):    
    TOKEN = vk_token
    @Handler(Filter().in_text("Привет"))
    async def cab1(cls, message:BaseMsg):
        await message.answer("Hello")
    @Handler()
    async def cab2(cls, message:BaseMsg):

        user:Sender = await message.send_inline_kboard
        print(user.first_name)
        print("ФОТО:  ", message.photo)
        print("ДОКУМЕНТ:  ", message.document)
        print("АУДИО:  ", message.audio)
        print("ГОЛОСОВОЕ:  ", message.voice)
        print("ВИДЕО:  ", message.video)
        print("ТЕКСТ:  ", message.text)
        print("data:  ", message.date)


class TGEcho(Echo, AiogramComponent):
    TOKEN = tgram_token

    @Handler(Filter().in_text("hi"))
    async def cab2(cls, message:BaseMsg):
        await message.send_inline_kboard(message, keyboard=Keyboard([ [["name", "adata"], ["name","data"]] ]),text="инлайн клавиатура")
    @Handler(Filter().text("hello"))
    async def cab3(cls, message:BaseMsg):
        await message.answer(message, "Кфбинет №22")

import asyncio
print("works")
asyncio.run(start_bots())