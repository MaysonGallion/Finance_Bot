import asyncio
import aioschedule as schedule
from datetime import datetime, timedelta
from metody_db import Database
from config import bot

database = Database('database_1.db')


async def remind_planned_incomes():
    current_time = datetime.now()
    planned_incomes = database.get_all_planned_incomes()

    for income in planned_incomes:
        income_id = income[0]
        user_id = income[1]  # Идентификатор пользователя получаем из информации о доходе
        category_name = income[2]
        amount = income[3]
        income_date = datetime.fromtimestamp(income[4])
        repeat_period = income[5]

        remind_interval = None

        if repeat_period == 1:
            remind_interval = timedelta(days=1)
        elif repeat_period == 2:
            remind_interval = timedelta(days=3)
        elif repeat_period == 3:
            remind_interval = timedelta(days=7)
        elif repeat_period == 4:
            remind_interval = timedelta(days=30)
        elif repeat_period == 5:
            continue

        if income_date - current_time <= remind_interval:
            await bot.send_message(user_id,
                                   f"Вы запланировали получить доход '{category_name}' на сумму {amount} через {income_date - current_time}")


async def remind_planned_expense():
    current_time = datetime.now()
    planned_expenses = database.get_all_planned_expenses()

    for expense in planned_expenses:
        expense_id = expense[0]
        user_id = expense[1]  # Идентификатор пользователя получаем из информации о доходе
        category_name = expense[2]
        amount = expense[3]
        expense_date = datetime.fromtimestamp(expense[4])
        repeat_period = expense[5]

        remind_interval = None

        if repeat_period == 1:
            remind_interval = timedelta(days=1)
        elif repeat_period == 2:
            remind_interval = timedelta(days=3)
        elif repeat_period == 3:
            remind_interval = timedelta(days=7)
        elif repeat_period == 4:
            remind_interval = timedelta(days=30)
        elif repeat_period == 5:
            continue

        if expense_date - current_time <= remind_interval:
            await bot.send_message(user_id,
                                   f"Вы запланировали расход '{category_name}' на сумму {amount} через {expense_date - current_time}")


async def process_received_incomes():
    current_time = datetime.now()
    planned_incomes = database.get_all_planned_incomes()

    for income in planned_incomes:
        income_id = income[0]
        user_id = income[1]
        category_name = income[2]
        amount = income[3]
        income_date = datetime.fromtimestamp(income[4])
        repeat_period = income[5]

        if current_time >= income_date:
            database.add_income(user_id, category_name, amount, income_date.timestamp())
            balance = database.get_user_balance(user_id)
            balance += amount
            database.update_user_balance(user_id, balance)
            database.delete_planned_income(income_id)
            await bot.send_message(user_id, f"Запланированный доход '{category_name}' на сумму {amount} был получен.")


async def process_received_expense():
    current_time = datetime.now()
    planned_expenses = database.get_all_planned_expenses()

    for expense in planned_expenses:
        expense_id = expense[0]
        user_id = expense[1]
        category_name = expense[2]
        amount = expense[3]
        expense_date = datetime.fromtimestamp(expense[4])
        repeat_period = expense[5]

        if current_time >= expense_date:
            database.add_expense(user_id, category_name, amount, expense_date.timestamp())
            balance = database.get_user_balance(user_id)
            balance -= amount
            database.update_user_balance(user_id, balance)
            database.delete_planned_income(expense_id)
            await bot.send_message(user_id, f"Запланированный расход '{category_name}' на сумму {amount} был получен.")


async def job_scheduler():
    schedule.every().day.at("00:00").do(
        remind_planned_incomes)
    schedule.every().day.at("00:00").do(
        process_received_incomes)
    schedule.every().day.at("00:00").do(
        remind_planned_expense)
    schedule.every().day.at("00:00").do(
        process_received_expense)

    while True:
        await schedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(dp):
    await dp.start_polling()
    dp.loop.create_task(job_scheduler())
