import os
import psycopg2
from psycopg2 import Error
from psycopg2.extras import RealDictCursor
from datetime import date
import hashlib
import binascii


class Database:
    """
    Database helper for Hotel schema:
      guest, guest_address, guest_phone,
      room,
      employee, employee_phone,
      reservation, reservation_room,
      employee_guest
    """

    def __init__(self):
        self.db_url = os.environ.get("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable is not set")

    def get_connection(self):
        """Create a DB connection (dict rows)."""
        try:
            return psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)
        except Error as e:
            print(f"Error connecting to database: {e}")
            raise

    # ---------------------------
    # Password hashing (PBKDF2)
    # ---------------------------
    def _hash_password(self, password: str) -> str:
        """Hash password with PBKDF2-HMAC-SHA512. Output format: salt(64hex) + hash(hex)."""
        salt = hashlib.sha256(os.urandom(60)).hexdigest().encode("ascii")  # 64 hex chars
        pwdhash = hashlib.pbkdf2_hmac("sha512", password.encode("utf-8"), salt, 100000)
        pwdhash = binascii.hexlify(pwdhash)
        return (salt + pwdhash).decode("ascii")

    def verify_password(self, stored_password: str, provided_password: str) -> bool:
        """
        Verify password.
        Backward-compatible:
          - if stored_password looks like PBKDF2 format => verify hashed
          - else => treat as plain text (legacy)
        """
        if not stored_password:
            return False

        # Detect our hashed format (salt length 64, hex)
        if len(stored_password) >= 64:
            salt = stored_password[:64]
            rest = stored_password[64:]
            # if rest is hex-ish then assume hashed format
            if all(c in "0123456789abcdef" for c in (salt + rest).lower()):
                try:
                    pwdhash = hashlib.pbkdf2_hmac(
                        "sha512",
                        provided_password.encode("utf-8"),
                        salt.encode("ascii"),
                        100000,
                    )
                    pwdhash = binascii.hexlify(pwdhash).decode("ascii")
                    return pwdhash == rest
                except Exception:
                    # fallback to plain if anything odd
                    return stored_password == provided_password

        return stored_password == provided_password

    # ---------------------------
    # Generic execution helpers
    # ---------------------------
    def execute(self, query: str, params=None, fetch=False, fetchone=False):
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query, params)
                result = None
                if fetchone:
                    result = cur.fetchone()
                elif fetch:
                    result = cur.fetchall()
                conn.commit()
                return result
        except Error:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ---------------------------
    # Schema init (optional)
    # ---------------------------
    def init_db(self):
        """
        Create hotel tables if they do not exist (safe for fresh DB).
        If your Neon already has tables/data, calling this won't destroy anything.
        """
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                # guest
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS guest (
                        guest_id SERIAL PRIMARY KEY,
                        name VARCHAR(50) NOT NULL,
                        family VARCHAR(50) NOT NULL,
                        national_id VARCHAR(20),
                        passport VARCHAR(20),
                        birthdate DATE NOT NULL,
                        email VARCHAR(100) UNIQUE NOT NULL,
                        CONSTRAINT chk_guest_id
                        CHECK (national_id IS NOT NULL OR passport IS NOT NULL)
                    );
                    """
                )

                # guest_address
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS guest_address (
                        address_id SERIAL PRIMARY KEY,
                        guest_id INT NOT NULL,
                        province VARCHAR(50) NOT NULL,
                        city VARCHAR(50) NOT NULL,
                        street VARCHAR(100) NOT NULL,
                        plaque VARCHAR(20) NOT NULL,
                        CONSTRAINT fk_guest_address
                        FOREIGN KEY (guest_id)
                        REFERENCES guest(guest_id)
                        ON DELETE CASCADE
                    );
                    """
                )

                # guest_phone
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS guest_phone (
                        phone_id SERIAL PRIMARY KEY,
                        guest_id INT NOT NULL,
                        phone VARCHAR(20) NOT NULL,
                        CONSTRAINT uq_guest_phone UNIQUE (guest_id, phone),
                        CONSTRAINT fk_guest_phone
                        FOREIGN KEY (guest_id)
                        REFERENCES guest(guest_id)
                        ON DELETE CASCADE
                    );
                    """
                )

               
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS room (
                        room_id INT PRIMARY KEY,
                        type VARCHAR(30) NOT NULL,
                        capacity INT NOT NULL CHECK (capacity > 0),
                        price NUMERIC(10,2) NOT NULL CHECK (price >= 0),
                        features VARCHAR(255),
                        floor INT NOT NULL,
                        bed_type VARCHAR(30) NOT NULL,
                        smoking BOOLEAN NOT NULL DEFAULT FALSE,
                        status VARCHAR(20) NOT NULL,
                        CONSTRAINT chk_room_status
                        CHECK (status IN ('available','reserved','occupied','cleaning'))
                    );
                    """
                )

                # employee
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS employee (
                        emp_id SERIAL PRIMARY KEY,
                        name VARCHAR(50) NOT NULL,
                        family VARCHAR(50) NOT NULL,
                        national_id VARCHAR(20) UNIQUE NOT NULL,
                        birthdate DATE NOT NULL,
                        position VARCHAR(50) NOT NULL,
                        username VARCHAR(50) UNIQUE NOT NULL,
                        password VARCHAR(255) NOT NULL,
                        access_level INT NOT NULL CHECK (access_level BETWEEN 1 AND 5)
                    );
                    """
                )

                # employee_phone
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS employee_phone (
                        phone_id SERIAL PRIMARY KEY,
                        emp_id INT NOT NULL,
                        phone VARCHAR(20) NOT NULL,
                        CONSTRAINT uq_employee_phone UNIQUE (emp_id, phone),
                        CONSTRAINT fk_employee_phone
                        FOREIGN KEY (emp_id)
                        REFERENCES employee(emp_id)
                        ON DELETE CASCADE
                    );
                    """
                )

                # reservation
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS reservation (
                        res_id SERIAL PRIMARY KEY,
                        guest_id INT NOT NULL,
                        emp_id INT NOT NULL,
                        check_in DATE NOT NULL,
                        check_out DATE NOT NULL,
                        booking_date TIMESTAMP NOT NULL DEFAULT NOW(),
                        num_people INT NOT NULL CHECK (num_people > 0),
                        status VARCHAR(20) NOT NULL,
                        total_cost NUMERIC(10,2) NOT NULL CHECK (total_cost >= 0),
                        payment NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (payment >= 0),
                        discount NUMERIC(5,2) NOT NULL DEFAULT 0 CHECK (discount >= 0),
                        CONSTRAINT chk_reservation_dates CHECK (check_out > check_in),
                        CONSTRAINT chk_res_status CHECK (status IN ('active','canceled','finished')),
                        CONSTRAINT fk_res_guest FOREIGN KEY (guest_id) REFERENCES guest(guest_id),
                        CONSTRAINT fk_res_emp FOREIGN KEY (emp_id) REFERENCES employee(emp_id)
                    );
                    """
                )

                # reservation_room
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS reservation_room (
                        res_id INT NOT NULL,
                        room_id INT NOT NULL,
                        PRIMARY KEY (res_id, room_id),
                        CONSTRAINT fk_rr_res
                        FOREIGN KEY (res_id)
                        REFERENCES reservation(res_id)
                        ON DELETE CASCADE,
                        CONSTRAINT fk_rr_room
                        FOREIGN KEY (room_id)
                        REFERENCES room(room_id)
                    );
                    """
                )

                # employee_guest
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS employee_guest (
                        emp_id INT NOT NULL,
                        guest_id INT NOT NULL,
                        PRIMARY KEY (emp_id, guest_id),
                        CONSTRAINT fk_eg_emp
                        FOREIGN KEY (emp_id)
                        REFERENCES employee(emp_id)
                        ON DELETE CASCADE,
                        CONSTRAINT fk_eg_guest
                        FOREIGN KEY (guest_id)
                        REFERENCES guest(guest_id)
                        ON DELETE CASCADE
                    );
                    """
                )

                conn.commit()

            self.create_default_admin_employee()
            print("Hotel database schema ensured successfully.")

        except Error as e:
            print(f"Error initializing database: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def create_default_admin_employee(self):
        """
        Create default admin as an employee (if not exists).
        Uses env:
          ADMIN_USERNAME, ADMIN_PASSWORD
        Also needs defaults for employee required fields.
        """
        admin_username = os.environ.get("ADMIN_USERNAME", "admin")
        admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")


        default_emp = {
            "name": os.environ.get("ADMIN_NAME", "Admin"),
            "family": os.environ.get("ADMIN_FAMILY", "User"),
            "national_id": os.environ.get("ADMIN_NATIONAL_ID", "EMPADMIN0001"),
            "birthdate": os.environ.get("ADMIN_BIRTHDATE", "1990-01-01"),
            "position": os.environ.get("ADMIN_POSITION", "Manager"),
            "access_level": int(os.environ.get("ADMIN_ACCESS_LEVEL", "5")),
            "username": admin_username,
        }

        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT emp_id FROM employee WHERE username = %s", (admin_username,))
                if cur.fetchone():
                    return

                password_hash = self._hash_password(admin_password)

                cur.execute(
                    """
                    INSERT INTO employee (name, family, national_id, birthdate, position, username, password, access_level)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        default_emp["name"],
                        default_emp["family"],
                        default_emp["national_id"],
                        default_emp["birthdate"],
                        default_emp["position"],
                        default_emp["username"],
                        password_hash,
                        default_emp["access_level"],
                    ),
                )
                conn.commit()
                print(f"Default admin employee created: {admin_username}")
        except Error as e:
            conn.rollback()
            print(f"Error creating default admin employee: {e}")
           
        finally:
            conn.close()

    # ---------------------------
    # Auth
    # ---------------------------
    def authenticate_employee(self, username: str, password: str):
        """
        Authenticate using employee.username/password.
        Backward-compatible: if stored password is plain and matches, upgrade to hashed.
        Returns dict {emp_id, username, access_level, name, family, position} or None.
        """
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT emp_id, username, password, access_level, name, family, position
                    FROM employee
                    WHERE username = %s
                    """,
                    (username,),
                )
                emp = cur.fetchone()
                if not emp:
                    return None

                stored = emp["password"]
                ok = self.verify_password(stored, password)
                if not ok:
                    return None

             
                if stored == password:
                    try:
                        new_hash = self._hash_password(password)
                        cur.execute(
                            "UPDATE employee SET password = %s WHERE emp_id = %s",
                            (new_hash, emp["emp_id"]),
                        )
                        conn.commit()
                    except Error:
                        conn.rollback()

                return {
                    "emp_id": emp["emp_id"],
                    "username": emp["username"],
                    "access_level": emp["access_level"],
                    "name": emp["name"],
                    "family": emp["family"],
                    "position": emp["position"],
                }
        except Error as e:
            print(f"Error authenticating employee: {e}")
            return None
        finally:
            conn.close()

    # ---------------------------
    # Guests
    # ---------------------------
    def get_all_guests(self, limit=200):
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT guest_id, name, family, national_id, passport, birthdate, email
                    FROM guest
                    ORDER BY guest_id DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                return cur.fetchall()
        finally:
            conn.close()

    def get_guest_by_id(self, guest_id: int):
        return self.execute(
            """
            SELECT guest_id, name, family, national_id, passport, birthdate, email
            FROM guest
            WHERE guest_id = %s
            """,
            (guest_id,),
            fetchone=True,
        )

    def add_guest(self, name, family, national_id, passport, birthdate, email):
        if not (national_id or passport):
            raise ValueError("Either national_id or passport must be provided")
        return self.execute(
            """
            INSERT INTO guest (name, family, national_id, passport, birthdate, email)
            VALUES (%s,%s,%s,%s,%s,%s)
            RETURNING guest_id
            """,
            (name, family, national_id, passport, birthdate, email),
            fetchone=True,
        )["guest_id"]

    def update_guest_email(self, guest_id: int, email: str):
        self.execute(
            "UPDATE guest SET email = %s WHERE guest_id = %s",
            (email, guest_id),
        )

    def delete_guest(self, guest_id: int):
        self.execute("DELETE FROM guest WHERE guest_id = %s", (guest_id,))


    def get_guest_phones(self, guest_id: int):
        return self.execute(
            """
            SELECT phone_id, phone
            FROM guest_phone
            WHERE guest_id = %s
            ORDER BY phone_id DESC
            """,
            (guest_id,),
            fetch=True,
        )

    def add_guest_phone(self, guest_id: int, phone: str):
        return self.execute(
            """
            INSERT INTO guest_phone (guest_id, phone)
            VALUES (%s, %s)
            RETURNING phone_id
            """,
            (guest_id, phone),
            fetchone=True,
        )["phone_id"]

    def delete_guest_phone(self, phone_id: int):
        self.execute("DELETE FROM guest_phone WHERE phone_id = %s", (phone_id,))

    def get_guest_addresses(self, guest_id: int):
        return self.execute(
            """
            SELECT address_id, province, city, street, plaque
            FROM guest_address
            WHERE guest_id = %s
            ORDER BY address_id DESC
            """,
            (guest_id,),
            fetch=True,
        )

    def add_guest_address(self, guest_id: int, province: str, city: str, street: str, plaque: str):
        return self.execute(
            """
            INSERT INTO guest_address (guest_id, province, city, street, plaque)
            VALUES (%s,%s,%s,%s,%s)
            RETURNING address_id
            """,
            (guest_id, province, city, street, plaque),
            fetchone=True,
        )["address_id"]

    def delete_guest_address(self, address_id: int):
        self.execute("DELETE FROM guest_address WHERE address_id = %s", (address_id,))

    # ---------------------------
    # Rooms
    # ---------------------------
    def get_all_rooms(self, limit=200):
        return self.execute(
            """
            SELECT room_id, type, capacity, price, features, floor, bed_type, smoking, status
            FROM room
            ORDER BY room_id DESC
            LIMIT %s
            """,
            (limit,),
            fetch=True,
        )

    def get_room_by_id(self, room_id: int):
        return self.execute(
            """
            SELECT room_id, type, capacity, price, features, floor, bed_type, smoking, status
            FROM room
            WHERE room_id = %s
            """,
            (room_id,),
            fetchone=True,
        )

    def add_room(self, room_id: int, room_type: str, capacity: int, price, features: str, floor: int, bed_type: str, smoking: bool, status: str):
        return self.execute(
            """
            INSERT INTO room (room_id, type, capacity, price, features, floor, bed_type, smoking, status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (room_id, room_type, capacity, price, features, floor, bed_type, smoking, status),
        )

    def update_room_status(self, room_id: int, status: str):
        self.execute(
            "UPDATE room SET status = %s WHERE room_id = %s",
            (status, room_id),
        )

    def delete_room(self, room_id: int):
        self.execute("DELETE FROM room WHERE room_id = %s", (room_id,))

    def get_available_rooms(self, check_in: str = None, check_out: str = None, limit=200):
        """
        Simple availability:
          - returns rooms with status='available'
        If you want date-based availability (not in reserved date range),
        we can extend later using reservation + reservation_room overlap logic.
        """
        return self.execute(
            """
            SELECT room_id, type, capacity, price, floor, bed_type, smoking, status
            FROM room
            WHERE status = 'available'
            ORDER BY room_id
            LIMIT %s
            """,
            (limit,),
            fetch=True,
        )

    # ---------------------------
    # Employees
    # ---------------------------
    def get_all_employees(self, limit=200):
        return self.execute(
            """
            SELECT emp_id, name, family, national_id, birthdate, position, username, access_level
            FROM employee
            ORDER BY emp_id DESC
            LIMIT %s
            """,
            (limit,),
            fetch=True,
        )

    def add_employee(
        self,
        name: str,
        family: str,
        national_id: str,
        birthdate: str,
        position: str,
        username: str,
        password: str,
        access_level: int,
        hash_password: bool = True,
    ):
        pw = self._hash_password(password) if hash_password else password
        return self.execute(
            """
            INSERT INTO employee (name, family, national_id, birthdate, position, username, password, access_level)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING emp_id
            """,
            (name, family, national_id, birthdate, position, username, pw, access_level),
            fetchone=True,
        )["emp_id"]

 
    def get_employee_phones(self, emp_id: int):
        return self.execute(
            """
            SELECT phone_id, phone
            FROM employee_phone
            WHERE emp_id = %s
            ORDER BY phone_id DESC
            """,
            (emp_id,),
            fetch=True,
        )

    def add_employee_phone(self, emp_id: int, phone: str):
        return self.execute(
            """
            INSERT INTO employee_phone (emp_id, phone)
            VALUES (%s, %s)
            RETURNING phone_id
            """,
            (emp_id, phone),
            fetchone=True,
        )["phone_id"]

    def delete_employee_phone(self, phone_id: int):
        self.execute("DELETE FROM employee_phone WHERE phone_id = %s", (phone_id,))

    def link_employee_guest(self, emp_id: int, guest_id: int):
        self.execute(
            """
            INSERT INTO employee_guest (emp_id, guest_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
            """,
            (emp_id, guest_id),
        )

    # ---------------------------
    # Reservations
    from psycopg2 import Error

    def create_reservation(
        self,
        guest_id: int,
        emp_id: int,
        check_in: str,
        check_out: str,
        num_people: int,
        status: str,
        total_cost,
        room_ids: list[int],
        payment=0,
        discount=0,
    ):
        """
        Create reservation + link rooms in reservation_room
        AND set room.status to 'reserved' when reservation is active.
        """

        if not room_ids:
            raise ValueError("At least one room_id is required")

      
        status = (status or "active").strip().lower()
        if status not in ("active", "canceled", "finished"):
            status = "active"

        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
    
                cur.execute(
                    """
                    SELECT room_id, status
                    FROM room
                    WHERE room_id = ANY(%s)
                    """,
                    (room_ids,),
                )
                rows = cur.fetchall()
                found_ids = {r["room_id"] for r in rows}
                missing = [rid for rid in room_ids if rid not in found_ids]
                if missing:
                    raise ValueError(f"اتاق(ها) پیدا نشدند: {missing}")

                not_available = [r["room_id"] for r in rows if r["status"] != "available"]
                if status == "active" and not_available:
                    raise ValueError(f"این اتاق‌ها available نیستند: {not_available}")

                
                cur.execute(
                    """
                    INSERT INTO reservation
                    (guest_id, emp_id, check_in, check_out, num_people, status, total_cost, payment, discount)
                    VALUES
                    (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    RETURNING res_id
                    """,
                    (guest_id, emp_id, check_in, check_out, num_people, status, total_cost, payment, discount),
                )
                res_id = cur.fetchone()["res_id"]

              
                cur.executemany(
                    """
                    INSERT INTO reservation_room (res_id, room_id)
                    VALUES (%s, %s)
                    """,
                    [(res_id, rid) for rid in room_ids],
                )

              
                if status == "active":
                    cur.execute(
                        """
                        UPDATE room
                        SET status = 'reserved'
                        WHERE room_id = ANY(%s)
                        """,
                        (room_ids,),
                    )

                conn.commit()
                return res_id

        except Error:
            conn.rollback()
            raise
        finally:
            conn.close()



    def get_reservation_by_id(self, res_id: int):
        return self.execute(
            """
            SELECT res_id, guest_id, emp_id, check_in, check_out, booking_date,
                   num_people, status, total_cost, payment, discount
            FROM reservation
            WHERE res_id = %s
            """,
            (res_id,),
            fetchone=True,
        )

    def get_reservation_rooms(self, res_id: int):
        return self.execute(
            """
            SELECT rr.room_id, r.type, r.capacity, r.price, r.status
            FROM reservation_room rr
            JOIN room r ON r.room_id = rr.room_id
            WHERE rr.res_id = %s
            ORDER BY rr.room_id
            """,
            (res_id,),
            fetch=True,
        )

    def list_active_reservations(self, limit=200):
        return self.execute(
            """
            SELECT r.res_id, r.guest_id, g.name, g.family, r.emp_id, e.username,
                   r.check_in, r.check_out, r.num_people, r.status, r.total_cost, r.payment, r.discount
            FROM reservation r
            JOIN guest g ON g.guest_id = r.guest_id
            JOIN employee e ON e.emp_id = r.emp_id
            WHERE r.status = 'active'
            ORDER BY r.res_id DESC
            LIMIT %s
            """,
            (limit,),
            fetch=True,
        )

    def add_payment(self, res_id: int, amount):
        """
        payment = payment + amount
        """
        self.execute(
            """
            UPDATE reservation
            SET payment = payment + %s
            WHERE res_id = %s
            """,
            (amount, res_id),
        )

    def set_reservation_status(self, res_id: int, status: str):
        self.execute(
            "UPDATE reservation SET status = %s WHERE res_id = %s",
            (status, res_id),
        )

    def delete_reservation(self, res_id: int):
        """
        reservation_room has ON DELETE CASCADE, so deleting reservation removes links too.
        """
        self.execute("DELETE FROM reservation WHERE res_id = %s", (res_id,))

    
    def cancel_reservation(self, res_id: int):
        """
        Set reservation status to canceled and free its rooms.
        """
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
            
                cur.execute("SELECT room_id FROM reservation_room WHERE res_id = %s", (res_id,))
                room_ids = [r["room_id"] for r in cur.fetchall()]

                
                cur.execute("UPDATE reservation SET status = 'canceled' WHERE res_id = %s", (res_id,))

                if room_ids:
                    cur.execute(
                        "UPDATE room SET status = 'available' WHERE room_id = ANY(%s)",
                        (room_ids,),
                    )

                conn.commit()
        except Error:
            conn.rollback()
            raise
        finally:
            conn.close()


    def finish_reservation(self, res_id: int):
        """
        Set reservation status to finished and free its rooms.
        """
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT room_id FROM reservation_room WHERE res_id = %s", (res_id,))
                room_ids = [r["room_id"] for r in cur.fetchall()]

                cur.execute("UPDATE reservation SET status = 'finished' WHERE res_id = %s", (res_id,))

                if room_ids:
                    cur.execute(
                        "UPDATE room SET status = 'available' WHERE room_id = ANY(%s)",
                        (room_ids,),
                    )

                conn.commit()
        except Error:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_cleaning_rooms(self, limit=50):
        return self.execute(
            """
            SELECT room_id, type, floor, bed_type, capacity, price, features
            FROM room
            WHERE status = 'cleaning'
            ORDER BY floor, room_id
            LIMIT %s
            """,
            (limit,),
            fetch=True,
        )

    # ---------------------------
    # Stats / Dashboard
    # ---------------------------
    def get_stats(self):
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS c FROM guest")
                total_guests = cur.fetchone()["c"]

                cur.execute("SELECT COUNT(*) AS c FROM room")
                total_rooms = cur.fetchone()["c"]

                cur.execute("SELECT COUNT(*) AS c FROM reservation WHERE status = 'active'")
                active_reservations = cur.fetchone()["c"]
=
                cur.execute(
                    """
                    SELECT COUNT(DISTINCT rr.room_id) AS c
                    FROM reservation_room rr
                    JOIN reservation r ON r.res_id = rr.res_id
                    WHERE r.status = 'active'
                    """
                )
                occupied_rooms = cur.fetchone()["c"] or 0

                available_rooms = max(0, total_rooms - occupied_rooms)

                cur.execute("SELECT COALESCE(SUM(payment),0) AS s FROM reservation")
                total_payments = cur.fetchone()["s"]

                cur.execute("SELECT COALESCE(SUM(total_cost),0) AS s FROM reservation")
                total_revenue = cur.fetchone()["s"]

                return {
                    "total_guests": total_guests,
                    "total_rooms": total_rooms,
                    "available_rooms": available_rooms,
                    "active_reservations": active_reservations,
                    "total_payments": float(total_payments),
                    "total_revenue": float(total_revenue),
                }
        except Error as e:
            print(f"Error getting stats: {e}")
            return {
                "total_guests": 0,
                "total_rooms": 0,
                "available_rooms": 0,
                "active_reservations": 0,
                "total_payments": 0,
                "total_revenue": 0,
            }
        finally:
            conn.close()

    def get_employee_by_id(self, emp_id: int):
        return self.execute(
            """
            SELECT emp_id, name, family, username, position, access_level, national_id, birthdate
            FROM employee
            WHERE emp_id = %s
            """,
            (emp_id,),
            fetchone=True,
        )



db = Database()