import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.client.session.aiohttp import AiohttpSession

# Logging setup
logging.basicConfig(level=logging.INFO)

# Bot token
bot_token = "Your_Bot_Token"  #Add your own telegram bot api

# Create a session
session = AiohttpSession()

# Initialize the Bot and Dispatcher
bot = Bot(token=bot_token, session=session)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Define FSM states
class Form(StatesGroup):
    language = State()
    name = State()
    course = State()
    subcourse = State()
    day = State()
    time = State()
    phone_number = State()
    confirmation = State()

# Courses and their channel IDs
courses = {
    "English": -1002289014372,
    "IT": -1002336411887,
    "Robotics": -1002297932865,
    "Mathematics": -1002313828384,
}

# Subcourses for each course
subcourses = {
    "English": {
        "ru": ["Английский для начинающих", "Английский для бизнеса"],
        "uz": ["Boshqaruv uchun ingliz tili", "Ingliz tilini o'rganish"]
    },
    "IT": {
        "ru": ["Программирование на Python", "Веб-разработка"],
        "uz": ["Python dasturlash", "Veb dasturlash"]
    },
    "Robotics": {
        "ru": ["Основы робототехники", "Программирование роботов"],
        "uz": ["Robototexnikaning asoslari", "Robotlarni dasturlash"]
    },
    "Mathematics": {
        "ru": ["Алгебра", "Геометрия"],
        "uz": ["Algebra", "Geometriya"]
    },
}

# Available times
times = ["9:00-11:00", "11:00-13:00", "14:00-16:00", "16:00-18:00"]

# Validate phone number format
async def validate_phone_number(phone_number: str) -> bool:
    return (phone_number.startswith("+998") and len(phone_number) == 13) or len(phone_number) == 9

# Start function to register handlers and start polling
async def start():
    dp.message.register(start_command, Command("start"))
    dp.message.register(handle_language, Form.language)
    dp.message.register(handle_name, Form.name)
    dp.callback_query.register(handle_course, Form.course)
    dp.callback_query.register(handle_subcourse, Form.subcourse)
    dp.callback_query.register(handle_day, Form.day)
    dp.callback_query.register(handle_time, Form.time)
    dp.message.register(handle_phone_number, Form.phone_number)
    dp.callback_query.register(handle_confirmation, Form.confirmation)

    await dp.start_polling(bot)

# Command handler for /start
@dp.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    await state.set_state(Form.language)
    language_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Русский", callback_data="language_ru"),
         InlineKeyboardButton(text="O'zbek", callback_data="language_uz")]
    ])
    await message.answer("Выберите язык / Tilni tanlang:", reply_markup=language_keyboard)

# Handle language selection
@dp.callback_query(lambda c: c.data.startswith("language_"))
async def handle_language(callback_query: types.CallbackQuery, state: FSMContext):
    language = "uz" if callback_query.data == "language_uz" else "ru"
    await state.update_data(language=language)

    await callback_query.message.answer(
        "Введите свое имя и фамилию:" if language == "ru" else "Ismingiz va familiyangizni kiriting:"
    )
    await state.set_state(Form.name)

# Handle name input
@dp.message(Form.name)
async def handle_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    data = await state.get_data()
    language = data.get("language", "ru")

    course_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=course, callback_data=course)] for course in courses.keys()
    ])
    await message.answer(
        "Какой курс вы выберете?" if language == "ru" else "Qaysi kursni tanlaysiz?", 
        reply_markup=course_keyboard
    )
    await state.set_state(Form.course)

# Handle course selection
@dp.callback_query(Form.course)
async def handle_course(callback_query: types.CallbackQuery, state: FSMContext):
    selected_course = callback_query.data
    await state.update_data(course=selected_course)
    data = await state.get_data()
    language = data.get("language", "ru")

    logging.info(f"Selected course: '{selected_course}'")
    subcourse_list = subcourses.get(selected_course, {}).get(language, [])

    if not subcourse_list:
        await callback_query.message.answer("Курс не найден!" if language == "ru" else "Kurs topilmadi!")
        return

    subcourse_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=subcourse, callback_data=subcourse)] for subcourse in subcourse_list
    ])
    await callback_query.message.answer(
        "Какой подкурс вы выберете?" if language == "ru" else "Qaysi subkursni tanlaysiz?", 
        reply_markup=subcourse_keyboard
    )
    await state.set_state(Form.subcourse)

# Handle subcourse selection
@dp.callback_query(Form.subcourse)
async def handle_subcourse(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(subcourse=callback_query.data)
    data = await state.get_data()
    language = data.get("language", "ru")

    await callback_query.answer(
        "Подкурс выбран!" if language == "ru" else "Subkurs tanlandi!"
    )
    await handle_day(callback_query, state)

# Handle day selection
@dp.callback_query(Form.day)
async def handle_day(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(day=callback_query.data)
    data = await state.get_data()
    language = data.get("language", "ru")

    time_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=time, callback_data=time)] for time in times
    ])
    await callback_query.message.answer(
        "Выберите время:" if language == "ru" else "Vaqtni tanlang:", 
        reply_markup=time_keyboard
    )
    await state.set_state(Form.time)

# Handle time selection
@dp.callback_query(Form.time)
async def handle_time(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(time=callback_query.data)
    data = await state.get_data()
    language = data.get("language", "ru")

    await callback_query.message.answer(
        "Введите свой номер телефона:" if language == "ru" else "Telefon raqamingizni kiriting:"
    )
    await state.set_state(Form.phone_number)

# Handle phone number input
@dp.message(Form.phone_number)
async def handle_phone_number(message: types.Message, state: FSMContext):
    phone_number = message.text
    language = (await state.get_data()).get("language", "ru")

    if await validate_phone_number(phone_number):
        if len(phone_number) == 9:
            phone_number = f"+998{phone_number}"

        await state.update_data(phone_number=phone_number)
        data = await state.get_data()

        user_data = {
            "name": data['name'],
            "course": data['course'],
            "subcourse": data['subcourse'],
            "day": data['day'],
            "time": data['time'],
            "phone_number": phone_number
        }
        
        confirmation_message = (
            f"Имя: {user_data['name']}\nКурс: {user_data['course']}\nПодкурс: {user_data['subcourse']}\nДень: {user_data['day']}\nВремя: {user_data['time']}\nТелефон: {user_data['phone_number']}"
            if language == "ru" else
            f"Ism: {user_data['name']}\nKurs: {user_data['course']}\nSubkurs: {user_data['subcourse']}\nKun: {user_data['day']}\nVaqti: {user_data['time']}\nTelefon: {user_data['phone_number']}"
        )
        
        confirmation_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Подтверждение", callback_data="confirm")],
            [InlineKeyboardButton(text="Отмена", callback_data="cancel")],
            [InlineKeyboardButton(text="Изменять", callback_data="modify")]
        ] if language == "ru" else [
            [InlineKeyboardButton(text="Tasdiqlash", callback_data="confirm")],
            [InlineKeyboardButton(text="Bekor qilish", callback_data="cancel")],
            [InlineKeyboardButton(text="O`zgartirish", callback_data="modify")]
        ])
        
        await message.answer(confirmation_message, reply_markup=confirmation_keyboard)
        await state.set_state(Form.confirmation)
    else:
        error_message = (
            "Пожалуйста, введите свой номер телефона в правильном формате!" if language == "ru" 
            else "Iltimos, telefon raqamingizni to'g'ri formatda kiriting!"
        )
        await message.answer(error_message)
# Handle confirmation
@dp.callback_query(Form.confirmation)
async def handle_confirmation(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "ru")
    channel_id = courses.get(data['course'])  # Get the channel ID for the selected course
    if callback_query.data == "confirm":
        if channel_id:
            try:
                await bot.send_message(channel_id, f"#Tasdiqlandi\n"
                                                   f"Ism: {data['name']}\n"
                                                   f"Kurs: {data['course']}\n"
                                                   f"Subkurs: {data['subcourse']}\n"
                                                   f"Kun: {data['day']}\n"
                                                   f"Vaqti: {data['time']}\n"
                                                   f"Telefon: {data['phone_number']}")
                if language=='ru':
                    confirmation_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Выбор курса", callback_data="restart")],
                    [InlineKeyboardButton(text="O нас", callback_data="about")]
                ])
                else:
                          confirmation_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Kurs tanlash", callback_data="restart")],
                    [InlineKeyboardButton(text="Biz haqimizda", callback_data="about")]
                ])
                if language=='ru':
                    await callback_query.message.answer("Ваша информация отправлена ​​на канал.", reply_markup=confirmation_keyboard)
                else:
                    await callback_query.message.answer("Ma'lumotlaringiz kanalga jo'natildi.", reply_markup=confirmation_keyboard)
            except Exception as e:
                await callback_query.message.answer("Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")
                logging.error(f"Error while sending message: {e}")
        await state.clear()
    elif callback_query.data == "cancel":
        if language=='ru':
                    cancellation_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Выбор курса", callback_data="restart")],
                    [InlineKeyboardButton(text="O нас", callback_data="about")]
                ])
        else:
                    cancellation_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Kurs tanlash", callback_data="restart")],
                    [InlineKeyboardButton(text="Biz haqimizda", callback_data="about")]
                ])
        if language=='ru':
            await callback_query.message.answer("Операция отменена.", reply_markup=cancellation_keyboard)
        else:
            await callback_query.message.answer("Operatsiya bekor qilindi.", reply_markup=cancellation_keyboard)
        await bot.send_message(channel_id,f"#Bekor_qilindi\n"
                                                   f"Ism: {data['name']}\n"
                                                   f"Kurs: {data['course']}\n"
                                                   f"Subkurs: {data['subcourse']}\n"
                                                   f"Kun: {data['day']}\n"
                                                   f"Vaqti: {data['time']}\n"
                                                   f"Telefon: {data['phone_number']}")
        await state.clear()
    elif callback_query.data == "modify":
        await start_command(callback_query.message, state)
        await bot.send_message(channel_id, f"#O`zgartirmoqchi\n"
                                                   f"Ism: {data['name']}\n"
                                                   f"Kurs: {data['course']}\n"
                                                   f"Subkurs: {data['subcourse']}\n"
                                                   f"Kun: {data['day']}\n"
                                                   f"Vaqti: {data['time']}\n"
                                                   f"Telefon: {data['phone_number']}")
# Handle restart and about options
@dp.callback_query(lambda c: c.data == "restart")
async def restart(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await start_command(callback_query.message, state)  # Restart the process

@dp.callback_query(lambda c: c.data == "about")
async def about(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "ru")
    
    if language == 'ru':
        about_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="FLIAL", callback_data="branches")],
            [InlineKeyboardButton(text="O`QITUVCHILAR", callback_data="teachers")]
        ])
    else:
        about_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="FLIAL", callback_data="branches")],
            [InlineKeyboardButton(text="O`QITUVCHILAR", callback_data="teachers")]
        ])

    await callback_query.message.answer("Biz haqimizda", reply_markup=about_keyboard)
# Handle branches and teachers options
@dp.callback_query(lambda c: c.data == "branches")
async def branches(callback_query: types.CallbackQuery):
    branches_info = (
        "1. Samarqand shahar, Firdavsiy 1/5 (Infin Bank)\n"
        "2. Samarqand shahar, Sattepo 55-maktab\n"
        "3. Samarqand shahar, Vagzal 139 (Rich burger)"
    )
    await callback_query.message.answer(branches_info)

@dp.callback_query(lambda c: c.data == "teachers")
async def teachers(callback_query: types.CallbackQuery):
    teachers_info = (
        "1. KHamroyeva Kumush - English (7.5 IELTS)\n"
        "2. Salimov Sardor - IT (Microsoft Sertifikat) \n"
        "3. Qo'chqorov Zoir - Math (A+ Sertifikat)\n"
        "4. Alisherov Akramboy - Math (A Sertifikat)"
    )
    await callback_query.message.answer(teachers_info)

# Start the bot
if __name__ == '__main__':
    asyncio.run(start())
