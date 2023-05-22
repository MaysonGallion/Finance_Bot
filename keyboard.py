from aiogram import types
from aiogram.types import KeyboardButton, InlineKeyboardButton

# Создаем объект клавиатуры
menu = types.InlineKeyboardMarkup(row_width=1)
profile_menu = types.InlineKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=1)
categories_income_menu = types.InlineKeyboardMarkup(row_width=1)
categories_expenses_menu = types.InlineKeyboardMarkup(row_width=1)
goals_menu = types.InlineKeyboardMarkup(resize_keyboard=True, row_width=1, one_time_keyboard=True)
planned_income_menu = types.InlineKeyboardMarkup(resize_keyboard=True, row_width=1, one_time_keyboard=True)
planned_expense_menu = types.InlineKeyboardMarkup(resize_keyboard=True, row_width=1, one_time_keyboard=True)
back_menu = types.InlineKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
back_menu_profile = types.InlineKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

# общие кнопки
back_btn = InlineKeyboardButton('🔙 Назад', callback_data='back')
income_btn = InlineKeyboardButton('💵 Доходы', callback_data='income')
expense_btn = InlineKeyboardButton('💸 Расходы', callback_data='expense')
categories_btn = InlineKeyboardButton('📂 Мои категории', callback_data='categories')
help_ = InlineKeyboardButton('❓ Помощь', callback_data='help')
my_profile_btn = InlineKeyboardButton('👤 Мой профиль', callback_data='profile')

# меню мой профиль
statistics_btn = InlineKeyboardButton('📈 Статистика', callback_data="statistics")
savings_btn = InlineKeyboardButton('🐖 Цели', callback_data="savings")
planned_payments_btn = InlineKeyboardButton('📆 Запланированные расходы', callback_data="planned_payments")
planned_income_btn = InlineKeyboardButton('📅 Запланированные доходы', callback_data="planned_income")

# меню запланированных доходов
view_planned_income_btn = InlineKeyboardButton('👀 Посмотреть мои запланированные доходы', callback_data="my_planned_income")
add_planned_income_btn = InlineKeyboardButton('➕ Запланировать доход', callback_data="created_planned_income")

# меню запланированные расходы
view_planned_expense_btn = InlineKeyboardButton('👀 Посмотреть мои запланированные расходы', callback_data="my_planned_expenses")
add_planned_expense_btn = InlineKeyboardButton('➕Запланировать расход', callback_data="created_planned_expenses")

# меню расходов и доходов
categories_income_btn = InlineKeyboardButton("💰 Мой доход", callback_data="my_income")
new_income_categories_btn = InlineKeyboardButton('➕ Создать новую категорию дохода',
                                                 callback_data="created_income_category")
categories_expenses_btn = InlineKeyboardButton('🧾 Мои расходы', callback_data="my_expense")
new_expenses_categories_btn = InlineKeyboardButton('➕ Создать новую категорию расхода',
                                                   callback_data="created_expense_category")

# меню целей
created_goals = InlineKeyboardButton('➕ Создать цель', callback_data="created_goals")
my_goals = InlineKeyboardButton('👀 Посмотреть мои цели', callback_data="my_goals")
back_to_profile_btn = InlineKeyboardButton('🔙 Назад к профилю', callback_data="back_profile")

menu.add(
    income_btn,
    expense_btn,
    categories_btn,
    my_profile_btn,
    help_,
)

categories_income_menu.add(
    categories_income_btn,
    new_income_categories_btn,
    back_btn,
)

categories_expenses_menu.add(
    categories_expenses_btn,
    new_expenses_categories_btn,
    back_btn,
)

profile_menu.add(
    statistics_btn,
    savings_btn,
    planned_income_btn,
    planned_payments_btn,
    back_btn,
)

goals_menu.add(
    my_goals,
    created_goals,
    back_to_profile_btn,
)
planned_income_menu.add(
    view_planned_income_btn,
    add_planned_income_btn,
    back_to_profile_btn,
)

planned_expense_menu.add(
    view_planned_expense_btn,
    add_planned_expense_btn,
    back_to_profile_btn,
)
back_menu.add(
    back_btn,
)
back_menu_profile.add(
    back_to_profile_btn,
)
