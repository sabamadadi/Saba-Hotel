from flask_login import LoginManager, UserMixin
from flask import redirect, url_for, flash
from database import db


class EmployeeUser(UserMixin):
    """
    Flask-Login user model mapped to employee table.
    employee schema fields we use:
      emp_id (PK), username, password, access_level, name, family, position
    """

    def __init__(self, emp_id, username, access_level=1, name=None, family=None, position=None):
        self.id = int(emp_id)
        self.username = username
        self.access_level = int(access_level) if access_level is not None else 1
        self.name = name
        self.family = family
        self.position = position

    def get_id(self):
        return str(self.id)

    @staticmethod
    def get(emp_id: int):
        """Load user by emp_id from DB."""
        try:
            emp_id = int(emp_id)
        except (TypeError, ValueError):
            return None

        try:
            emp = db.execute(
                """
                SELECT emp_id, username, access_level, name, family, position
                FROM employee
                WHERE emp_id = %s
                """,
                (emp_id,),
                fetchone=True,
            )
            if not emp:
                return None

            return EmployeeUser(
                emp_id=emp["emp_id"],
                username=emp["username"],
                access_level=emp.get("access_level", 1),
                name=emp.get("name"),
                family=emp.get("family"),
                position=emp.get("position"),
            )
        except Exception as e:
            print(f"Error loading employee user: {e}")
            return None

    @staticmethod
    def authenticate(username: str, password: str):
        """
        Authenticate user against employee.username/password.
        Uses db.authenticate_employee which supports hashed + legacy plain passwords.
        """
        try:
            username = (username or "").strip()
            if not username or not password:
                return None

            emp = db.authenticate_employee(username, password)
            if not emp:
                return None

            return EmployeeUser(
                emp_id=emp["emp_id"],
                username=emp["username"],
                access_level=emp.get("access_level", 1),
                name=emp.get("name"),
                family=emp.get("family"),
                position=emp.get("position"),
            )
        except Exception as e:
            print(f"Error authenticating employee: {e}")
            return None

login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login: load current user by id from session."""
    return EmployeeUser.get(user_id)


@login_manager.unauthorized_handler
def unauthorized():
    """Handle unauthorized access."""
    flash("لطفاً برای دسترسی به این صفحه وارد سیستم شوید.", "warning")

    return redirect(url_for("login"))
