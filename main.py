import logging
import keyboard
from datetime import datetime
from aiogram import types
from metody_db import Database
from config import bot, dp
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from data_control import on_startup

logging.basicConfig(level=logging.INFO)
database = Database("database_1.db")


class BalanceStates(StatesGroup):
    waiting_for_add_amount = State()
    waiting_for_minus_amount = State()


class CategState(StatesGroup):
    waiting_for_categ_name = State()


class ExpenseUpdatingStates(StatesGroup):
    category_name = State()
    amount = State()


class IncomeUpdatingStates(StatesGroup):
    category_name = State()
    amount = State()


class GoalInfo(StatesGroup):
    waiting_for_goal_name = State()
    waiting_for_goal_amount = State()
    waiting_for_goal_current_amount = State()
    waiting_for_goal_balance = State()
    waiting_for_new_balance = State()
    waiting_for_goal_update = State()


# для обработки запланированных доходов
class StateMachineForIncome(StatesGroup):
    income_name = State()
    income_amount = State()
    income_date = State()
    income_reminder = State()


class StateMachineForExpense(StatesGroup):
    expense_name = State()
    expense_amount = State()
    expense_date = State()
    expense_reminder = State()


class NewCategory(StatesGroup):
    waiting_for_income_category_name = State()
    waiting_for_income_amount = State()
    waiting_for_expenses_category_name = State()
    waiting_for_expenses_amount = State()


# обработчик команды старт
@dp.message_handler(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    user_exists = database.get_user(user_id)
    if not user_exists:
        registration_date = datetime.now()
        database.add_user(user_id, user_name, registration_date)
        database.add_user_balance(user_id, 0)  # добавляем баланс со значением 0
        await bot.send_message(chat_id=user_id,
                               text=f'Привет, {user_name}! Твой баланс: 0, перед началом использования бота сооветую заклянуть в "Помощь"',
                               reply_markup=keyboard.menu)
    else:
        balance = database.get_user_balance(user_id)
        if balance is not None:
            await bot.send_message(chat_id=user_id, text=f"С возвращением, {user_name}! Твой баланс: {balance}",
                                   reply_markup=keyboard.menu)
        else:
            # если баланс равен None, значит что-то пошло не так с базой данных
            await bot.send_message(chat_id=user_id, text="Что-то пошло не так. Попробуйте позже.")

    database.conn.commit()


# Меню доходы
@dp.callback_query_handler(text='income')
async def process_income_command(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text('Выберите действие:', reply_markup=keyboard.categories_income_menu)


# обработчик для посмотра доходов и напоминание что пользователь может изменить баланс уже для существующих целей
@dp.callback_query_handler(text='my_income')
async def show_my_income_categories(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    income_categories = database.get_all_income_categories(user_id)

    categories_text = "Ваши категории дохода:\n"
    for category_id, category_name in income_categories:
        balance = database.get_balance_by_income_category(user_id, category_id)
        categories_text += f"{category_name} - {balance}\n"

    await callback_query.message.edit_text(categories_text, reply_markup=keyboard.back_menu)
    await callback_query.message.answer(
        "Если вы хотите добавить сумму на баланс своих категории из списка выше, просто напишите ее название.")
    await IncomeUpdatingStates.category_name.set()


@dp.callback_query_handler(state=IncomeUpdatingStates.category_name, text='back')
async def go_back_to_main_menu(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback_query.message.answer('Главное меню', reply_markup=keyboard.menu)


@dp.message_handler(lambda message: message.text.lower() not in [c[1].lower() for c in
                                                                 database.get_all_income_categories(
                                                                     message.from_user.id)],
                    state=IncomeUpdatingStates.category_name)
async def process_wrong_category_name(message: types.Message):
    await message.reply("Категория отсутствует или некорректное название. Попробуйте еще раз.")


@dp.message_handler(lambda message: message.text.lower() in [c[1].lower() for c in
                                                             database.get_all_income_categories(message.from_user.id)],
                    state=IncomeUpdatingStates.category_name)
async def process_category_name(message: types.Message, state: FSMContext):
    await state.update_data(category_name=message.text)
    await message.answer("Введите сумму, которую вы хотите добавить(для дробных чисел используйте '.'):")
    await IncomeUpdatingStates.amount.set()


def is_float(value):
    try:
        temp_val = value.replace(",", ".")
        float(temp_val)
        return True
    except ValueError:
        return False


@dp.message_handler(lambda message: not is_float(message.text) or float(message.text.replace(",", ".")) < 0,
                    state=IncomeUpdatingStates.amount)
async def process_wrong_amount(message: types.Message):
    await message.reply("Введите корректную сумму (положительное число).")


@dp.message_handler(lambda message: is_float(message.text) and float(message.text.replace(",", ".")) >= 0,
                    state=IncomeUpdatingStates.amount)
async def process_amount(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    amount = float(message.text)
    user_data = await state.get_data()
    category_name = user_data["category_name"]

    category_id = database.get_category_id_by_name_income(category_name)
    database.add_income_for(user_id, category_id, amount)
    balance = database.get_user_balance(user_id)
    balance += amount
    database.update_user_balance(user_id, balance)

    await message.answer(
        f"Обновленный баланс категории {category_name} равен {balance}, текущий баланс пользователя равен {balance}.",
        reply_markup=keyboard.menu)

    await state.finish()


# меню расходы
@dp.callback_query_handler(text='expense')
async def process_expenses_command(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text('Выберите действие:', reply_markup=keyboard.categories_expenses_menu)


# выводим все расходы пользователя и напоминаем что он может изменять баланс для текущих категорий расхода
@dp.callback_query_handler(text='my_expense')
async def show_my_expense_categories(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    expense_categories = database.get_all_expense_categories(user_id)

    categories_text = "Ваши категории расходов:\n"
    for category_id, category_name in expense_categories:
        balance = database.get_balance_by_expense_category(user_id, category_id)
        categories_text += f"{category_name} - {balance}\n"

    await callback_query.message.edit_text(categories_text, reply_markup=keyboard.back_menu)
    await callback_query.message.answer(
        "Если вы хотите добавить сумму на баланс своих категории из списка выше, просто напишите ее название.",
    )
    await ExpenseUpdatingStates.category_name.set()


@dp.callback_query_handler(state=ExpenseUpdatingStates.category_name, text='back')
async def go_back_to_main_menu(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback_query.message.answer('Главное меню', reply_markup=keyboard.menu)


@dp.message_handler(lambda message: message.text.lower() not in [c[1].lower() for c in
                                                                 database.get_all_expense_categories(
                                                                     message.from_user.id)],
                    state=ExpenseUpdatingStates.category_name)
async def process_wrong_category_name(message: types.Message):
    await message.reply("Категория отсутствует или некорректное название. Попробуйте еще раз.")


@dp.message_handler(lambda message: message.text.lower() in [c[1].lower() for c in
                                                             database.get_all_expense_categories(message.from_user.id)],
                    state=ExpenseUpdatingStates.category_name)
async def process_category_name(message: types.Message, state: FSMContext):
    await state.update_data(category_name=message.text)
    await message.answer("Введите сумму, которую вы хотите добавить:")
    await ExpenseUpdatingStates.amount.set()


@dp.message_handler(lambda message: not is_float(message.text) or float(message.text.replace(",", ".")) < 0,
                    state=ExpenseUpdatingStates.amount)
async def process_wrong_amount(message: types.Message):
    await message.reply("Введите корректную сумму (положительное число).")


@dp.message_handler(lambda message: is_float(message.text) and float(message.text.replace(",", ".")) >= 0,
                    state=ExpenseUpdatingStates.amount)
async def process_amount(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    amount = float(message.text)
    user_data = await state.get_data()
    category_name = user_data["category_name"]

    category_id = database.get_category_id_by_name_expense(category_name)
    database.add_expense_for(user_id, category_id, amount)
    balance = database.get_user_balance(user_id)
    balance -= amount
    database.update_user_balance(user_id, balance)

    await message.answer(
        f"Обновленный баланс категории {category_name} равен {balance}, текущий баланс пользователя равен {balance}.",
        reply_markup=keyboard.menu)

    await state.finish()


# создаем категорию дохода её название
@dp.callback_query_handler(text='created_income_category')
async def create_new_income_categories(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text('Введите название категории дохода: ')
    await NewCategory.waiting_for_income_category_name.set()


# создаем категорию расхода её название
@dp.callback_query_handler(text='created_expense_category')
async def create_new_expenses_categories(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text('Введите названия категории расхода: ')
    await NewCategory.waiting_for_expenses_category_name.set()


# создается баланс для категории доходов
@dp.message_handler(state=NewCategory.waiting_for_income_category_name)
async def process_category_name(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    category_name = message.text
    database.add_income_category(user_id, category_name)
    await state.update_data(category_name=category_name)
    await NewCategory.waiting_for_income_amount.set()
    await message.answer("Введите сумму дохода:")


# создается баланс для категории расхода
@dp.message_handler(state=NewCategory.waiting_for_expenses_category_name)
async def process_category_name(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    category_name = message.text
    database.add_expense_category(user_id, category_name)
    await state.update_data(category_name=category_name)
    await NewCategory.waiting_for_expenses_amount.set()
    await message.answer("Введите сумму расхода: ")


# сохраняем категория дохода и обновляем базу данных
@dp.message_handler(state=NewCategory.waiting_for_income_amount)
async def income_amount(message: types.Message, state: FSMContext):
    amount = float(message.text)
    user_id = message.from_user.id
    data = await state.get_data()
    category_name = data.get("category_name")
    category_id = database.get_category_id_by_name_income(category_name)
    print(category_name, category_id)
    data_income = datetime.now()
    database.add_income(user_id, category_id, amount, data_income)

    balance = database.get_user_balance(user_id)
    balance += amount
    database.update_user_balance(user_id, balance)
    await message.answer(f"Доход в размере {amount} для категории \"{category_name}\" успешно добавлен. "
                         f"Ваш новый баланс: {balance}",
                         reply_markup=keyboard.menu)
    await state.finish()
    database.conn.commit()


# сохраняем категорию расхода и обновляем базу данных
@dp.message_handler(state=NewCategory.waiting_for_expenses_amount)
async def expenses_amount(message: types.Message, state: FSMContext):
    amount = float(message.text)
    user_id = message.from_user.id
    data = await state.get_data()
    category_name = data.get("category_name")
    category_id = database.get_category_id_by_name_expense(category_name)
    data_expenses = datetime.now()
    database.add_expense(user_id, category_id, amount, data_expenses)

    balance = database.get_user_balance(user_id)
    balance -= amount
    database.update_user_balance(user_id, balance)
    await message.answer(f"Расход в размере {amount} для категории \"{category_name}\" успешно добавлен. "
                         f"Ваш новый баланс: {balance}",
                         reply_markup=keyboard.menu)
    await state.finish()
    database.conn.commit()


# обработчик отвечающий за вывод всех категорий (дохода и расхода)категорий
@dp.callback_query_handler(text='categories')
async def show_my_categories(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    income_categories = database.get_all_income_categories(user_id)
    expense_categories = database.get_all_expense_categories(user_id)

    income_categories_text = "Ваши категории дохода:\n"
    for category_id, category_name in income_categories:
        balance = database.get_balance_by_income_category(user_id, category_id)
        income_categories_text += f"{category_name} - {balance}\n"

    expense_categories_text = "Ваши категории расхода:\n"
    for category_id, category_name in expense_categories:
        balance = database.get_balance_by_expense_category(user_id, category_id)
        expense_categories_text += f"{category_name} - {balance}\n"

    await callback_query.message.edit_text(f"{income_categories_text}\n{expense_categories_text}",
                                           reply_markup=keyboard.back_menu)


# обработка команды мой профиль
@dp.callback_query_handler(text='profile')
async def show_profile_menu(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_name = callback_query.from_user.full_name

    balance = database.get_user_balance(user_id)
    total_expenses = database.get_total_expenses(user_id)
    total_income = database.get_total_income(user_id)

    profile_info = f"Привет, {user_name}!\n"
    profile_info += f"Твой баланс: {balance}\n"
    profile_info += f"Твой расход за все время: {total_expenses}\n"
    profile_info += f"Твой доход за все время: {total_income}\n"

    await callback_query.message.edit_text(profile_info, reply_markup=keyboard.profile_menu)


# обработка статистики
@dp.callback_query_handler(text='statistics')
async def show_statistics(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    # Получаем общий доход за текущий месяц
    total_income = database.get_monthly_income(user_id)
    # Получаем общие расходы за текущий месяц
    total_expenses = database.get_monthly_expenses(user_id)
    # Получаем категории дохода с балансом за текущий месяц
    income_categories = database.get_monthly_income_by_category(user_id)
    # Получаем категории расходов с балансом за текущий месяц
    expenses_categories = database.get_monthly_expenses_by_category(user_id)
    current_mont = datetime.now().strftime("%B")
    # Формируем сообщение со статистикой
    message_text = f"Вот ваша статистика за {current_mont}:\n"
    message_text += f"Доход ({total_income}):\n"
    for category, balance in income_categories:
        message_text += f"{category} - {balance}\n"

    message_text += f"\nРасход ({total_expenses}):\n"
    for category, balance in expenses_categories:
        message_text += f"{category} - {balance}\n"

    # Отправляем сообщение с статистикой
    await callback_query.message.edit_text(message_text, reply_markup=keyboard.back_menu_profile)


# обработчик для открытия меню для ЗАПЛАНИРОВАНЫХ ДОХОДОВ

@dp.callback_query_handler(lambda c: c.data == 'planned_income')
async def planned_income(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.edit_text('Выберите действие:', reply_markup=keyboard.planned_income_menu)


# обработчик для открытия меню для ЗАПЛАНИРОВАННЫХ ДОХОДОВ
@dp.callback_query_handler(lambda c: c.data == 'planned_payments')
async def planned_expense(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.edit_text('Выберите действие:', reply_markup=keyboard.planned_expense_menu)


# обработчик чтобы посмотреть уже СУЩЕСТВУЮЩИЕ запланированные ДОХОДЫ
@dp.callback_query_handler(lambda c: c.data == 'my_planned_income')
async def view_planned_income(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    planned_incomes = database.get_planned_incomes(user_id)
    if not planned_incomes:
        await bot.send_message(user_id, 'У вас пока нет запланированных доходов.', reply_markup=keyboard.profile_menu)
    else:
        incomes_message = 'Ваши запланированные доходы:\n'
        for income in planned_incomes:
            incomes_message += f"{income['category_name']} - {income['amount']} (получение {income['date']})\n"
        await bot.send_message(user_id, incomes_message, reply_markup=keyboard.profile_menu)


# обработчик чтобы посмотреть уже СУЩЕСТВУЮЩИЕ запланированные РАСХОДЫ
@dp.callback_query_handler(lambda c: c.data == 'my_planned_expenses')
async def view_planned_expense(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    planned_expenses = database.get_planned_expenses(user_id)
    if not planned_expenses:
        await bot.send_message(user_id, 'У вас пока нет запланированных расходов', reply_markup=keyboard.profile_menu)
    else:
        expenses_message = 'Ваши запланированные расходы:\n'
        for expense in planned_expenses:
            expenses_message += f"{expense['category_name']} - {expense['amount']} (расход {expense['date']})\n"
        await bot.send_message(user_id, expenses_message, reply_markup=keyboard.profile_menu)


# обработчик для СОЗДАНИЕ новых запланированых ДОХОДОВ, (тут мы принимаем название)
@dp.callback_query_handler(lambda c: c.data == 'created_planned_income')
async def add_planned_income(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await StateMachineForIncome.income_name.set()
    await bot.send_message(callback_query.from_user.id, 'Введите название для вашего запланированного дохода:')


# обработчик для СОЗДАНИЕ новых запланированых РАСХОДОВ, (тут мы принимаем название)
@dp.callback_query_handler(lambda c: c.data == 'created_planned_expenses')
async def add_planned_expense(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await StateMachineForExpense.expense_name.set()
    await bot.send_message(callback_query.from_user.id, 'Введите название для вашего запланированного расхода:')


# принимаем сумму для запланированного дохода
@dp.message_handler(state=StateMachineForIncome.income_name)
async def process_income_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['income_name'] = message.text
    await StateMachineForIncome.next()
    await message.answer('Введите сумму для вашего запланированного дохода:')


# принимаем сумму для запланированного расхода
@dp.message_handler(state=StateMachineForExpense.expense_name)
async def process_expense_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['expense_name'] = message.text
    await StateMachineForExpense.next()
    await message.answer('Введите сумму для вашего запланированного расхода:')


# принимаем ДАТУ окончания для запланированного ДОХОДА
@dp.message_handler(state=StateMachineForIncome.income_amount)
async def process_income_amount(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['income_amount'] = message.text
    await StateMachineForIncome.next()
    await message.answer('Введите дату (в формате день.месяц.год), когда вы ожидаете получить этот доход.')


# принимаем ДАТУ окончания для запланированного РАСХОДА
@dp.message_handler(state=StateMachineForExpense.expense_amount)
async def process_expense_amount(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['expense_amount'] = message.text
    await StateMachineForExpense.next()
    await message.answer('Введите дату (в формате день.месяц.год), когда вы ожидаете этот расход.')


# принимаем ПЕРЕОДИЧНОСТЬ ПОВТОРЕНИЙ окончания для запланированного ДОХОДА
@dp.message_handler(state=StateMachineForIncome.income_date)
async def process_income_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['income_date'] = message.text
    await StateMachineForIncome.next()
    await message.answer(
        'Сколько раз вам нужно напоминать об этом доходе? Вы можете выбрать из следующих вариантов'
        '(Отправте число от 1 до 5):'
        '\n1. Раз в день'
        '\n2. Раз в три дня'
        '\n3. Раз в неделю'
        '\n4. Раз в месяц'
        '\n5.Не напоминать')


# принимаем ПЕРЕОДИЧНОСТЬ ПОВТОРЕНИЙ окончания для запланированного РАСХОДА
@dp.message_handler(state=StateMachineForExpense.expense_date)
async def process_expense_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['expense_date'] = message.text
    await StateMachineForExpense.next()
    await message.answer(
        'Сколько раз вам нужно напоминать об этом расходе? Вы можете выбрать из следующих вариантов'
        '(Отправте число от 1 до 5):'
        '\n1. Раз в день'
        '\n2. Раз в три дня'
        '\n3. Раз в неделю'
        '\n4. Раз в месяц'
        '\n5.Не напоминать')


# сохраняем в таблицу изменения о ЗАПЛАНИРОВАННЫХ ДОХОДАХ
@dp.message_handler(state=StateMachineForIncome.income_reminder)
async def process_income_reminder(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        reminder = message.text
        if reminder.isdigit() and 1 <= int(reminder) <= 5:
            data['income_reminder'] = reminder
            user_id = message.from_user.id
            category_id = database.get_category_id(user_id, data['income_name'])
            database.add_planned_income(
                user_id,
                category_id,
                data['income_amount'],
                data['income_date'],
                data['income_reminder']
            )
            await state.finish()
            await message.answer('Ваш запланированный доход успешно добавлен.',
                                 reply_markup=keyboard.planned_income_menu)
        else:
            await message.answer('Пожалуйста, введите число от 1 до 5.')


# сохраняем в таблицу изменения о ЗАПЛАНИРОВАННЫХ РАСХОДАХ
@dp.message_handler(state=StateMachineForExpense.expense_reminder)
async def process_expense_reminder(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        reminder = message.text
        if reminder.isdigit() and 1 <= int(reminder) <= 5:
            data['expense_reminder'] = reminder
            user_id = message.from_user.id
            category_id = database.get_category_id_expenses(user_id, data['expense_name'])
            database.add_planned_expense(
                user_id,
                category_id,
                data['expense_amount'],
                data['expense_date'],
                data['expense_reminder']
            )
            await state.finish()
            await message.answer('Ваш запланированный расход успешно добавлен.',
                                 reply_markup=keyboard.planned_expense_menu)
        else:
            await message.answer('Пожалуйста, введите число от 1 до 5.')


# Обработчик для открытия меню для ЦЕЛЕЙ
@dp.callback_query_handler(lambda c: c.data == 'savings')
async def goals(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.edit_text('Пожалуйста выберите:', reply_markup=keyboard.goals_menu)


# Этот обработчик вызывается, когда пользователь решает создать новую цель. Он начинает процесс, спрашивая название цели.
@dp.callback_query_handler(lambda c: c.data == 'created_goals')
async def process_goals_command(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 'Укажите название цели:', reply_markup=keyboard.back_menu_profile)
    await GoalInfo.waiting_for_goal_name.set()


# Здесь обработчик принимает название цели и спрашивает сумму цели.
@dp.message_handler(state=GoalInfo.waiting_for_goal_name)
async def process_goal_name(message: types.Message, state: FSMContext):
    goal_name = message.text
    await state.update_data(goal_name=goal_name)
    await message.answer('Укажите сумму цели')
    await GoalInfo.waiting_for_goal_amount.set()


# Здесь обработчик принимает сумму цели и спрашивает текущую сумму для цели.
@dp.message_handler(state=GoalInfo.waiting_for_goal_amount)
async def process_goal_amount(message: types.Message, state: FSMContext):
    goal_amount = float(message.text)
    await state.update_data(goal_amount=goal_amount)
    await message.answer('Укажите текущую сумму цели:')
    await GoalInfo.waiting_for_goal_current_amount.set()


# Этот обработчик принимает текущую сумму цели и сохраняет все данные о цели в базу данных.
@dp.message_handler(state=GoalInfo.waiting_for_goal_current_amount)
async def process_goal_current_amount(message: types.Message, state: FSMContext):
    goal_current_amount = float(message.text)
    user_id = message.from_user.id
    data = await state.get_data()
    goal_name = data.get("goal_name")
    goal_amount = data.get("goal_amount")
    database.add_goal(user_id, goal_name, goal_amount, goal_current_amount)
    await message.answer('Цель успешно добавлена!', reply_markup=keyboard.back_menu_profile)
    await state.finish()


# Этот обработчик вызывается, когда пользователь хочет посмотреть свои текущие цели. Он показывает все цели пользователя и предлагает обновить баланс для существующих целей.
# Этот обработчик вызывается, когда пользователь хочет посмотреть свои текущие цели. Он показывает все цели пользователя и предлагает обновить баланс для существующих целей.
@dp.callback_query_handler(lambda c: c.data == 'my_goals')
async def show_user_goals(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    # Получаем цели пользователя
    goals = database.get_user_goals(user_id)

    if goals:
        goals_text = "Ваши активные цели:\n"
        for goal in goals:
            _, goal_name, amount, current_amount = goal
            goals_text += f"Название: {goal_name}\n"
            goals_text += f"Сумма: {amount}\n"
            goals_text += f"Текущая сумма: {current_amount}\n\n"

        # Получаем выполненные цели пользователя
        completed_goals = database.get_completed_goals(user_id)
        if completed_goals:
            goals_text += "Ваши выполненные цели:\n"
            for goal in completed_goals:
                _, goal_name, amount, _ = goal
                goals_text += f"Название: {goal_name}\n"
                goals_text += f"Сумма: {amount}\n\n"

        await bot.send_message(callback_query.from_user.id, goals_text, reply_markup=keyboard.back_menu_profile)
        await bot.send_message(callback_query.from_user.id,
                               'Чтобы обновить баланс к текущей сумме цели напишите навания цели (учитывайте верхний или нижний регистр букв)')
        await GoalInfo.waiting_for_goal_update.set()  # Переходим в состояние ожидания обновления баланса для цели
    else:
        await bot.send_message(callback_query.from_user.id, "У вас пока нет активных целей.",
                               reply_markup=keyboard.back_menu_profile)


# Этот обработчик вызывается, когда пользователь хочет вернуться к профилю из меню целей.
@dp.callback_query_handler(state=GoalInfo.waiting_for_goal_update, text='back_profile')
async def go_back_to_profile_menu(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback_query.message.answer('Мой профиль: ', reply_markup=keyboard.profile_menu)


@dp.callback_query_handler(text='back_profile')
async def go_back_to_profile_menu_without_state(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text('Мой профиль: ', reply_markup=keyboard.profile_menu)


# Этот обработчик вызывается, когда пользователь хочет обновить баланс для существующей цели. Он спрашивает новый баланс для цели.
@dp.message_handler(state=GoalInfo.waiting_for_goal_update)
async def update_goal_balance(message: types.Message, state: FSMContext):
    goal_name = message.text
    user_id = message.from_user.id

    # Получаем цель пользователя по названию
    goal = database.get_goal_by_name(user_id, goal_name)

    if goal:
        await message.answer("Введите новый баланс для цели:")
        await GoalInfo.waiting_for_new_balance.set()
        await state.update_data(goal_id=goal[0])
    else:
        await message.answer("Цель с таким названием не найдена.")


# Этот обработчик принимает новый баланс для цели и обновляет его в базе данных.
@dp.message_handler(state=GoalInfo.waiting_for_new_balance)
async def set_new_goal_balance(message: types.Message, state: FSMContext):
    new_balance = float(message.text)
    data = await state.get_data()
    goal_id = data.get("goal_id")

    # Обновляем баланс для цели
    current_balance = database.get_goal_balance(goal_id)
    update_balance = current_balance + new_balance
    database.update_goal_balance(goal_id, update_balance)

    goal = database.get_goal_by_id(goal_id)

    if goal:
        goal_name, amount, current_amount = goal
        await message.answer(
            f"Для цели \"{goal_name}\" обновлен баланс. Текущая сумма: {current_amount}, Общая сумма: {amount}",
            reply_markup=keyboard.profile_menu)
        if current_amount >= amount:
            await message.answer(f"Поздравляю! Вы собрали нужную сумму для цели \"{goal_name}\"")
    else:
        await message.answer("Не удалось обновить баланс для цели.")

    await state.finish()


# обработка выхода в главное меню
@dp.callback_query_handler(text='back', state='*')
async def go_back_to_main_menu(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text('Вы вернулись главное меню:', reply_markup=keyboard.menu)


@dp.message_handler(commands=['add_balance'], state="*")
async def add_balance(message: types.Message):
    await message.answer('Введите сумму, которую хотите добавить:')
    await BalanceStates.waiting_for_add_amount.set()


@dp.message_handler(state=BalanceStates.waiting_for_add_amount)
async def process_add_balance(message: types.Message, state: FSMContext):
    amount = float(message.text)
    database.update_user_balance(message.chat.id, database.get_user_balance(message.chat.id) + amount)
    await message.answer('Баланс успешно обновлен.')
    await state.finish()


@dp.message_handler(commands=['minus_balance'], state="*")
async def minus_balance(message: types.Message):
    await message.answer('Введите сумму, которую хотите отнять:')
    await BalanceStates.waiting_for_minus_amount.set()


@dp.message_handler(state=BalanceStates.waiting_for_minus_amount)
async def process_minus_balance(message: types.Message, state: FSMContext):
    amount = float(message.text)
    database.update_user_balance(message.chat.id, database.get_user_balance(message.chat.id) - amount)
    await message.answer('Баланс успешно обновлен.')
    await state.finish()


@dp.message_handler(commands=['delete_categ'], state="*")
async def delete_categ(message: types.Message):
    await message.answer('Введите название категории для удаления:')
    await CategState.waiting_for_categ_name.set()


@dp.message_handler(state=CategState.waiting_for_categ_name)
async def process_delete_categ(message: types.Message, state: FSMContext):
    category_name = message.text
    category_id_income = database.get_category_id_by_name_income(category_name)
    category_id_expense = database.get_category_id_by_name_expense(category_name)
    if category_id_income is not None:
        database.delete_income_records(category_id_income)
        database.delete_income_category(category_id_income)
    if category_id_expense is not None:
        database.delete_expense_records(category_id_expense)
        database.delete_expense_category(category_id_expense)
    await message.answer('Категория успешно удалена.')
    await state.finish()


@dp.message_handler(commands=['balance'], state="*")
async def balance(message: types.Message):
    user_balance = database.get_user_balance(message.chat.id)
    await message.answer(f"Ваш баланс: {user_balance}.")


@dp.message_handler(commands=['my_categories'], state="*")
async def categories(message: types.Message):
    user_id = message.from_user.id
    income_categories = database.get_all_income_categories(user_id)
    expense_categories = database.get_all_expense_categories(user_id)

    income_categories_text = "Ваши категории дохода:\n"
    for category_id, category_name in income_categories:
        balance = database.get_balance_by_income_category(user_id, category_id)
        income_categories_text += f"{category_name} - {balance}\n"

    expense_categories_text = "Ваши категории расхода:\n"
    for category_id, category_name in expense_categories:
        balance = database.get_balance_by_expense_category(user_id, category_id)
        expense_categories_text += f"{category_name} - {balance}\n"

    await message.answer(f"{income_categories_text}\n{expense_categories_text}",
                         reply_markup=keyboard.back_menu)


@dp.message_handler(commands=['my_income'], state="*")
async def show_my_income(message: types.Message):
    user_id = message.from_user.id
    income_categories = database.get_all_income_categories(user_id)

    categories_text = "Ваши категории дохода:\n"
    for category_id, category_name in income_categories:
        balance = database.get_balance_by_income_category(user_id, category_id)
        categories_text += f"{category_name} - {balance}\n"

    await message.answer(categories_text, reply_markup=keyboard.back_menu)


@dp.message_handler(commands=['my_expenses'], state="*")
async def show_my_expense(message: types.Message):
    user_id = message.from_user.id
    expense_categories = database.get_all_expense_categories(user_id)

    categories_text = "Ваши категории расходов:\n"
    for category_id, category_name in expense_categories:
        balance = database.get_balance_by_expense_category(user_id, category_id)
        categories_text += f"{category_name} - {balance}\n"

    await message.answer(categories_text, reply_markup=keyboard.back_menu)


@dp.callback_query_handler(text='help')
async def help_(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text(
        'Вот список быстрых команд которые тебе погут в использовании бота:\n'
        '/start - перезагрузить бота.\n'
        '/add_balance - добавить сумму к балансу.\n'
        '/minus_balance - отнять сумму от баланса.\n'
        '/delete_categ - удалить категорию(в название категории стоит учитывать регистр).\n'
        '/my_categories - просмотреть категории.\n'
        '/balance - проверить баланс.\n'
        '/my_income - проверить свои доходы.\n'
        '/my_expenses - проверить свои расходы.\n'
        'Так же ты можешь изменять баланс для каждой из своих категорий в меню доходов и расходов\nпри просмотре своих категорий.',
        reply_markup=keyboard.back_menu)


if __name__ == '__main__':
    from aiogram import executor

    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
