import sqlite3
from datetime import datetime, timedelta


class Database:
    def __init__(self, database_1):
        self.conn = sqlite3.connect('database_1.db')
        self.cursor = self.conn.cursor()

    def add_user(self, user_id, user_name, registration_date, balance=0):
        # метод для добавления пользователя в таблицу базы данных
        with self.conn:
            registration_date = registration_date.strftime("%d/%m/%Y")
            self.cursor.execute("INSERT INTO users (user_id, user_name, registration_date) VALUES (?, ?, ?)",
                                (user_id, user_name, registration_date))

    def get_user(self, user_id):
        # метод для получения пользователя из таблицы базы данных
        with self.conn:
            self.cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            result = self.cursor.fetchone()
            return result

    def add_user_balance(self, user_id, balance):
        # метод для добавления баланса пользователя в таблицу базы данных
        query = "INSERT OR IGNORE INTO user_balance (user_id, balance) VALUES (?, ?)"
        self.cursor.execute(query, (user_id, balance))
        self.conn.commit()

    def update_user_balance(self, user_id, balance):
        query = "UPDATE user_balance SET balance = ? WHERE user_id = ?"
        self.cursor.execute(query, (balance, user_id))
        self.conn.commit()

    def get_user_balance(self, user_id):
        # метод для получения баланса пользователя из таблицы базы данных
        query = "SELECT balance FROM user_balance WHERE user_id = ?"
        self.cursor.execute(query, (user_id,))
        result = self.cursor.fetchone()
        if result is not None:
            return result[0]
        else:
            return 0

    def add_income_category(self, user_id, category_name):
        query = "INSERT INTO categories_of_income (user_id, category_name) VALUES (?, ?)"
        self.cursor.execute(query, (user_id, category_name,))
        self.conn.commit()

    def add_expense_category(self, user_id, category_name):
        query = "INSERT INTO categories_of_expenses (user_id, category_name) VALUES (?, ?)"
        self.cursor.execute(query, (user_id, category_name,))
        self.conn.commit()

    def get_category_id_by_name_income(self, category_name):
        query = "SELECT category_id FROM categories_of_income WHERE category_name = ?"
        self.cursor.execute(query, (category_name,))
        result = self.cursor.fetchone()
        if result is not None:
            return result[0]
        else:
            return None

    def get_category_id_by_name_expense(self, category_name):
        query = "SELECT category_id FROM categories_of_expenses WHERE category_name = ?"
        self.cursor.execute(query, (category_name,))
        result = self.cursor.fetchone()
        if result is not None:
            return result[0]
        else:
            return None

    def add_income(self, user_id, category_id, amount, date):
        query = "INSERT INTO income (user_id, category_id, amount, date) VALUES (?, ?, ?, ?)"
        self.cursor.execute(query, (user_id, category_id, amount, date))
        self.conn.commit()

    def add_expense(self, user_id, category_id, amount, date):
        query = "INSERT INTO expenses (user_id, category_id, amount, date) VALUES (?, ?, ?, ?)"
        self.cursor.execute(query, (user_id, category_id, amount, date))
        self.conn.commit()

    def get_all_income_categories(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT category_id, category_name FROM categories_of_income WHERE user_id = ?", (user_id,))
        return cursor.fetchall()

    def get_all_expense_categories(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT category_id, category_name FROM categories_of_expenses WHERE user_id = ?", (user_id,))
        return cursor.fetchall()

    def get_balance_by_income_category(self, user_id, category_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT SUM(amount) FROM income WHERE user_id = ? AND category_id = ?", (user_id, category_id))
        return cursor.fetchone()[0]

    def get_balance_by_expense_category(self, user_id, category_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT SUM(amount) FROM expenses WHERE user_id = ? AND category_id = ?", (user_id, category_id))
        return cursor.fetchone()[0]

    def get_total_expenses(self, user_id):
        query = "SELECT SUM(amount) FROM expenses WHERE user_id = ?"
        self.cursor.execute(query, (user_id,))
        result = self.cursor.fetchone()
        if result is not None:
            return result[0]
        else:
            return 0

    def get_total_income(self, user_id):
        query = "SELECT SUM(amount) FROM income WHERE user_id = ?"
        self.cursor.execute(query, (user_id,))
        result = self.cursor.fetchone()
        if result is not None:
            return result[0]
        else:
            return 0

    def get_monthly_income(self, user_id):
        # Метод для получения общего дохода за текущий месяц
        now = datetime.now()
        start_of_month = datetime(now.year, now.month, 1).date()
        end_of_month = start_of_month + timedelta(days=32 - start_of_month.day)

        query = "SELECT SUM(amount) FROM income WHERE user_id = ? AND date >= ? AND date < ?"
        self.cursor.execute(query, (user_id, start_of_month, end_of_month))
        result = self.cursor.fetchone()
        return result[0] if result[0] is not None else 0

    def get_monthly_expenses(self, user_id):
        # Метод для получения общих расходов за текущий месяц
        now = datetime.now()
        start_of_month = datetime(now.year, now.month, 1).date()
        end_of_month = start_of_month + timedelta(days=32 - start_of_month.day)

        query = "SELECT SUM(amount) FROM expenses WHERE user_id = ? AND date >= ? AND date < ?"
        self.cursor.execute(query, (user_id, start_of_month, end_of_month))
        result = self.cursor.fetchone()
        return result[0] if result[0] is not None else 0

    def get_monthly_income_by_category(self, user_id):
        # Метод для получения категорий дохода с балансом за текущий месяц
        now = datetime.now()
        start_of_month = datetime(now.year, now.month, 1).date()
        end_of_month = start_of_month + timedelta(days=32 - start_of_month.day)

        query = """
            SELECT c.category_name, SUM(i.amount)
            FROM income i
            INNER JOIN categories_of_income c ON i.category_id = c.category_id
            WHERE i.user_id = ? AND i.date >= ? AND i.date < ?
            GROUP BY i.category_id
            """
        self.cursor.execute(query, (user_id, start_of_month, end_of_month))
        result = self.cursor.fetchall()
        return result

    def get_monthly_expenses_by_category(self, user_id):
        # Метод для получения категорий расходов с балансом за текущий месяц
        now = datetime.now()
        start_of_month = datetime(now.year, now.month, 1).date()
        end_of_month = start_of_month + timedelta(days=32 - start_of_month.day)

        query = """
            SELECT c.category_name, SUM(e.amount)
            FROM expenses e
            INNER JOIN categories_of_expenses c ON e.category_id = c.category_id
            WHERE e.user_id = ? AND e.date >= ? AND e.date < ?
            GROUP BY e.category_id
            """
        self.cursor.execute(query, (user_id, start_of_month, end_of_month))
        result = self.cursor.fetchall()
        return result

    def add_goal(self, user_id, goal_name, goal_amount, goal_current_amount):
        self.cursor.execute("""
            INSERT INTO goals (user_id, goals_name, amount, current_amount, status)
            VALUES (?, ?, ?, ?, 'active')
        """, (user_id, goal_name, goal_amount, goal_current_amount))
        self.conn.commit()

    def get_user_goals(self, user_id):
        self.cursor.execute("""
            SELECT goals_id, goals_name, amount, current_amount
            FROM goals
            WHERE user_id = ? AND status = 'active'
        """, (user_id,))
        return self.cursor.fetchall()

    def get_goal_by_name(self, user_id, goal_name):
        query = "SELECT * FROM goals WHERE user_id = ? AND goals_name = ?"
        self.cursor.execute(query, (user_id, goal_name))
        result = self.cursor.fetchone()
        return result

    def get_completed_goals(self, user_id):
        self.cursor.execute("""
            SELECT goals_id, goals_name, amount, current_amount
            FROM goals
            WHERE user_id = ? AND status = 'completed'
        """, (user_id,))
        return self.cursor.fetchall()

    def get_goal_balance(self, goal_id):
        self.cursor.execute("""
                    SELECT current_amount
                    FROM goals
                    WHERE goals_id = ?
                """, (goal_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def update_goal_balance(self, goal_id, new_balance):
        self.cursor.execute("""
            UPDATE goals
            SET current_amount = ?,
            status = CASE WHEN ? >= amount THEN 'completed' ELSE 'active' END
            WHERE goals_id = ?
        """, (new_balance, new_balance, goal_id))
        self.conn.commit()

    def get_goal_by_id(self, goal_id):
        query = "SELECT goals_name, amount, current_amount FROM goals WHERE goals_id = ?"
        self.cursor.execute(query, (goal_id,))
        result = self.cursor.fetchone()
        return result

    def get_incomes_by_category_id(self, category_id, user_id):
        self.cursor.execute("SELECT * FROM income WHERE category_id=? AND user_id=?", (category_id, user_id))
        incomes = self.cursor.fetchall()
        return incomes

    def add_income_for(self, user_id, category_id, amount):
        query = "INSERT INTO income (user_id, category_id, amount, date) VALUES (?, ?, ?, ?)"
        current_date = datetime.now()  # получаем текущую дату в формате Unix timestamp
        self.cursor.execute(query, (user_id, category_id, amount, current_date))
        self.conn.commit()

    def add_expense_for(self, user_id, category_id, amount):
        date = datetime.now()
        query = """INSERT INTO expenses (user_id, category_id, amount, date) VALUES (?, ?, ?, ?)"""
        self.cursor.execute(query, (user_id, category_id, amount, date))
        self.conn.commit()

    def get_planned_incomes(self, user_id):
        self.cursor.execute("""
            SELECT categories_of_income.category_name, planned_income.amount, planned_income.date
            FROM planned_income 
            INNER JOIN categories_of_income ON planned_income.category_id = categories_of_income.category_id
            WHERE planned_income.user_id = ?
            """, (user_id,))
        rows = self.cursor.fetchall()
        return [dict(zip(["category_name", "amount", "date"], row)) for row in rows]

    def get_planned_expenses(self, user_id):
        self.cursor.execute("""
        SELECT categories_of_expenses.category_name, planned_expenses.amount, planned_expenses.date
        FROM planned_expenses
        INNER JOIN categories_of_expenses ON planned_expenses.category_id = categories_of_expenses.category_id
        WHERE planned_expenses.user_id = ?
        """, (user_id,))
        rows = self.cursor.fetchall()
        return [dict(zip(["category_name", "amount", "date"], row)) for row in rows]

    def add_planned_income(self, user_id, category_id, amount, date, repeat_period):
        query = """
        INSERT INTO planned_income (user_id, category_id, amount, date, repeat_period)
        VALUES (?, ?, ?, ?, ?)
        """
        self.cursor.execute(query, (user_id, category_id, amount, date, repeat_period))
        self.conn.commit()

    def add_planned_expense(self, user_id, category_id, amount, date, repeat_period):
        query = """
        INSERT INTO planned_expenses (user_id, category_id, amount, date, repeat_period)
        VALUES (?, ?, ?, ?, ?)
        """
        self.cursor.execute(query, (user_id, category_id, amount, date, repeat_period))
        self.conn.commit()

    def get_category_id(self, user_id, category_name):
        query = """
        SELECT category_id FROM categories_of_income 
        WHERE user_id = ? AND category_name = ?
        """
        self.cursor.execute(query, (user_id, category_name))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        else:
            # Если категория не найдена, мы можем создать новую
            self.cursor.execute(
                "INSERT INTO categories_of_income (category_name, user_id) VALUES (?, ?)",
                (category_name, user_id)
            )
            self.conn.commit()
            return self.cursor.lastrowid

    def get_category_id_expenses(self, user_id, category_name):
        query = """
        SELECT category_id FROM categories_of_expenses
        WHERE user_id = ? AND category_name = ?
        """
        self.cursor.execute(query, (user_id, category_name))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        else:
            self.cursor.execute(
                "INSERT INTO categories_of_expenses (category_name, user_id) VALUES (?, ?)",
                (category_name, user_id)
            )
            self.conn.commit()
            return self.cursor.lastrowid

    def delete_planned_income(self, income_id):
        self.cursor.execute("DELETE FROM planned_incomes WHERE id = ?", (income_id,))
        self.conn.commit()

    def delete_planned_expense(self, expense_id):
        self.cursor.execute("DELETE FROM planned_expenses WHERE id = ?", (expense_id,))
        self.conn.commit()

    def get_all_planned_incomes(self):
        with self.conn:
            return self.cursor.execute("SELECT * FROM planned_income").fetchall()

    def get_all_planned_expenses(self):
        with self.conn:
            return self.cursor.execute("SELECT * FROM planned_expenses").fetchall()

    def delete_income_records(self, category_id):
        self.cursor.execute("""
            DELETE FROM income
            WHERE category_id = ?
        """, (category_id,))
        self.conn.commit()

    def delete_expense_records(self, category_id):
        self.cursor.execute("""
            DELETE FROM expenses
            WHERE category_id = ?
        """, (category_id,))
        self.conn.commit()

    def delete_income_category(self, category_id):
        self.cursor.execute("""
            DELETE FROM categories_of_income
            WHERE category_id = ?
        """, (category_id,))
        self.conn.commit()

    def delete_expense_category(self, category_id):
        self.cursor.execute("""
            DELETE FROM categories_of_expenses
            WHERE category_id = ?
        """, (category_id,))
        self.conn.commit()
