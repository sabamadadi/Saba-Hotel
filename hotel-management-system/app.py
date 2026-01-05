import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_required, logout_user, current_user
from dotenv import load_dotenv
from flask_login import login_user


load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")

from database import db
from auth import EmployeeUser, login_manager 

login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "لطفاً برای دسترسی به این صفحه وارد سیستم شوید."


@app.context_processor
def inject_now():
    return {"now": datetime.now(), "current_date": datetime.now()}


@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()

        if not username or not password:
            flash("لطفاً نام کاربری و رمز عبور را وارد کنید.", "danger")
            return render_template("login.html")

        user = EmployeeUser.authenticate(username, password)
        if user:

            login_user(user, remember=True)

            session["emp_id"] = user.id
            session["username"] = user.username
            session["access_level"] = user.access_level
            flash("ورود موفقیت‌آمیز بود!", "success")

            next_page = request.args.get("next")
            if next_page:
                return redirect(next_page)
            return redirect(url_for("dashboard"))

        flash("نام کاربری یا رمز عبور اشتباه است.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    if current_user.is_authenticated:
        logout_user()
    flash("با موفقیت از سیستم خارج شدید.", "info")
    return redirect(url_for("login"))

@app.route("/api/stats")
@login_required
def api_stats():
    stats = db.get_stats()

    return jsonify(
        {
            "total_guests": stats.get("total_guests", 0),
            "total_rooms": stats.get("total_rooms", 0),
            "available_rooms": stats.get("available_rooms", 0),
            "active_reservations": stats.get("active_reservations", 0),
            "total_payments": stats.get("total_payments", 0),
            "total_revenue": stats.get("total_revenue", 0),
        }
    )

@app.route("/guests")
@login_required
def guests():
    guests_list = db.get_all_guests()
    return render_template("guests.html", guests=guests_list)


@app.route("/guests/add", methods=["GET", "POST"])
@login_required
def add_guest():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        family = (request.form.get("family") or "").strip()
        national_id = (request.form.get("national_id") or "").strip() or None
        passport = (request.form.get("passport") or "").strip() or None
        birthdate = (request.form.get("birthdate") or "").strip()
        email = (request.form.get("email") or "").strip()

    
        if not name or len(name) < 2:
            flash("نام باید حداقل ۲ حرف باشد.", "danger")
            return render_template("add_guest.html")

        if not family or len(family) < 2:
            flash("نام خانوادگی باید حداقل ۲ حرف باشد.", "danger")
            return render_template("add_guest.html")

        if not (national_id or passport):
            flash("حداقل یکی از national_id یا passport باید پر باشد.", "danger")
            return render_template("add_guest.html")

        if not birthdate:
            flash("تاریخ تولد الزامی است.", "danger")
            return render_template("add_guest.html")

        if not email or "@" not in email:
            flash("ایمیل معتبر وارد کنید.", "danger")
            return render_template("add_guest.html")

        try:
            guest_id = db.add_guest(name, family, national_id, passport, birthdate, email)
            flash(f'مهمان "{name} {family}" با موفقیت اضافه شد. کد مهمان: {guest_id}', "success")
            return redirect(url_for("guests"))
        except Exception as e:
            flash(f"خطا در افزودن مهمان: {str(e)}", "danger")

    return render_template("add_guest.html")


@app.route("/guests/<int:guest_id>/delete")
@login_required
def delete_guest(guest_id):
    try:
        g = db.get_guest_by_id(guest_id)
        if not g:
            flash("مهمان یافت نشد.", "danger")
        else:
            db.delete_guest(guest_id)
            flash(f'مهمان "{g["name"]} {g["family"]}" حذف شد.', "success")
    except Exception as e:
        flash(f"خطا در حذف مهمان: {str(e)}", "danger")

    return redirect(url_for("guests"))
    
@app.route("/rooms")
@login_required
def rooms():
    rooms_list = db.get_all_rooms()
    return render_template("rooms.html", rooms=rooms_list)


@app.route("/rooms/add", methods=["GET", "POST"])
@login_required
def add_room():
    if request.method == "POST":
        
        room_id = (request.form.get("room_id") or "").strip()
        room_type = (request.form.get("type") or "").strip()
        capacity = (request.form.get("capacity") or "").strip()
        price = (request.form.get("price") or "").strip()
        features = (request.form.get("features") or "").strip() or None
        floor = (request.form.get("floor") or "").strip()
        bed_type = (request.form.get("bed_type") or "").strip()
        smoking = (request.form.get("smoking") or "false").strip().lower() in ("true", "1", "yes", "on")
        status = (request.form.get("status") or "available").strip()

       
        try:
            room_id = int(room_id)
        except Exception:
            flash("کد اتاق (room_id) باید عدد باشد.", "danger")
            return render_template("add_room.html")

        if not room_type:
            flash("نوع اتاق الزامی است.", "danger")
            return render_template("add_room.html")

        try:
            capacity = int(capacity)
            if capacity <= 0:
                raise ValueError()
        except Exception:
            flash("ظرفیت باید عدد مثبت باشد.", "danger")
            return render_template("add_room.html")

        try:
            price = float(price)
            if price < 0:
                raise ValueError()
        except Exception:
            flash("قیمت باید عدد معتبر باشد.", "danger")
            return render_template("add_room.html")

        try:
            floor = int(floor)
        except Exception:
            flash("طبقه باید عدد باشد.", "danger")
            return render_template("add_room.html")

        if not bed_type:
            flash("نوع تخت الزامی است.", "danger")
            return render_template("add_room.html")

        try:
            db.add_room(room_id, room_type, capacity, price, features, floor, bed_type, smoking, status)
            flash(f"اتاق #{room_id} با موفقیت اضافه شد.", "success")
            return redirect(url_for("rooms"))
        except Exception as e:
            flash(f"خطا در افزودن اتاق: {str(e)}", "danger")

    return render_template("add_room.html")


@app.route("/rooms/<int:room_id>/status", methods=["POST"])
@login_required
def update_room_status(room_id):
    status = (request.form.get("status") or "").strip()
    if not status:
        flash("وضعیت جدید را وارد کنید.", "danger")
        return redirect(url_for("rooms"))
    try:
        db.update_room_status(room_id, status)
        flash(f"وضعیت اتاق #{room_id} بروزرسانی شد.", "success")
    except Exception as e:
        flash(f"خطا در بروزرسانی وضعیت اتاق: {str(e)}", "danger")
    return redirect(url_for("rooms"))


@app.route("/rooms/<int:room_id>/delete")
@login_required
def delete_room(room_id):
    try:
        r = db.get_room_by_id(room_id)
        if not r:
            flash("اتاق یافت نشد.", "danger")
        else:
            db.delete_room(room_id)
            flash(f"اتاق #{room_id} حذف شد.", "success")
    except Exception as e:
        flash(f"خطا در حذف اتاق: {str(e)}", "danger")
    return redirect(url_for("rooms"))



@app.route("/reservations")
@login_required
def reservations():
   
    res_list = db.list_active_reservations()
    return render_template("reservations.html", reservations=res_list)


@app.route("/dashboard")
@login_required
def dashboard():
    stats = db.get_stats()

    =
    recent_activities = [
        {"title": "رزرو جدید ثبت شد", "time": "چند دقیقه پیش", "description": "رزرو جدید توسط کارمند ثبت شد"},
        {"title": "مهمان جدید اضافه شد", "time": "امروز", "description": "یک مهمان جدید در سیستم ثبت شد"},
        {"title": "اتاق بروزرسانی شد", "time": "امروز", "description": "وضعیت یک اتاق تغییر کرد"},
    ]

    cleaning_rooms = db.get_cleaning_rooms(limit=200)

    return render_template(
        "dashboard.html",
        stats=stats,
        recent_activities=recent_activities,
        cleaning_rooms=cleaning_rooms,
    )

@app.route("/reservations/add", methods=["GET", "POST"])
@login_required
def add_reservation():
    if request.method == "POST":
        guest_id = (request.form.get("guest_id") or "").strip()
        check_in = (request.form.get("check_in") or "").strip()
        check_out = (request.form.get("check_out") or "").strip()
        num_people = (request.form.get("num_people") or "1").strip()
        total_cost = (request.form.get("total_cost") or "0").strip()
        payment = (request.form.get("payment") or "0").strip()
        discount = (request.form.get("discount") or "0").strip()
        status = (request.form.get("status") or "active").strip()


        room_ids = request.form.getlist("room_ids")

        try:
            guest_id = int(guest_id)
        except Exception:
            flash("guest_id باید عدد باشد.", "danger")
            return redirect(url_for("add_reservation"))

        if not check_in or not check_out:
            flash("تاریخ ورود و خروج الزامی است.", "danger")
            return redirect(url_for("add_reservation"))

        try:
            num_people = int(num_people)
            if num_people <= 0:
                raise ValueError()
        except Exception:
            flash("تعداد نفرات باید عدد مثبت باشد.", "danger")
            return redirect(url_for("add_reservation"))

        try:
            total_cost = float(total_cost)
            payment = float(payment)
            discount = float(discount)
        except Exception:
            flash("مقادیر مالی باید عدد باشند.", "danger")
            return redirect(url_for("add_reservation"))

        if not room_ids:
            flash("حداقل یک اتاق انتخاب کنید.", "danger")
            return redirect(url_for("add_reservation"))

        try:
            room_ids = [int(x) for x in room_ids]
        except Exception:
            flash("شناسه اتاق‌ها باید عدد باشند.", "danger")
            return redirect(url_for("add_reservation"))

        try:
            emp_id = int(getattr(current_user, "id"))
            res_id = db.create_reservation(
                guest_id=guest_id,
                emp_id=emp_id,
                check_in=check_in,
                check_out=check_out,
                num_people=num_people,
                status=status,
                total_cost=total_cost,
                room_ids=room_ids,
                payment=payment,
                discount=discount,
            )
            flash(f"رزرو با موفقیت ثبت شد. کد رزرو: {res_id}", "success")
            return redirect(url_for("reservations"))
        except Exception as e:
            flash(f"خطا در ثبت رزرو: {str(e)}", "danger")


    guests_list = db.get_all_guests(limit=500)
    available_rooms = db.get_available_rooms(limit=500)
    return render_template("add_reservation.html", guests=guests_list, rooms=available_rooms)


@app.route("/reservations/<int:res_id>/cancel")
@login_required
def cancel_reservation(res_id):
    try:
        db.set_reservation_status(res_id, "canceled")
        flash(f"رزرو {res_id} لغو شد.", "success")
    except Exception as e:
        flash(f"خطا در لغو رزرو: {str(e)}", "danger")
    return redirect(url_for("reservations"))


@app.route("/reservations/<int:res_id>/finish")
@login_required
def finish_reservation(res_id):
    try:
        db.set_reservation_status(res_id, "finished")
        flash(f"رزرو {res_id} پایان یافت.", "success")
    except Exception as e:
        flash(f"خطا در پایان رزرو: {str(e)}", "danger")
    return redirect(url_for("reservations"))

@app.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        current_password = (request.form.get("current_password") or "").strip()
        new_password = (request.form.get("new_password") or "").strip()
        confirm_password = (request.form.get("confirm_password") or "").strip()

        if not current_password or not new_password or not confirm_password:
            flash("لطفاً تمام فیلدها را پر کنید.", "danger")
            return render_template("change_password.html")

        if new_password != confirm_password:
            flash("رمز عبور جدید و تأیید آن مطابقت ندارند.", "danger")
            return render_template("change_password.html")

        if len(new_password) < 6:
            flash("رمز عبور جدید باید حداقل ۶ حرف باشد.", "danger")
            return render_template("change_password.html")

        try:
            
            emp = db.authenticate_employee(current_user.username, current_password)
            if not emp:
                flash("رمز عبور فعلی اشتباه است.", "danger")
                return render_template("change_password.html")

           
            new_hash = db._hash_password(new_password) 
            db.execute("UPDATE employee SET password = %s WHERE emp_id = %s", (new_hash, current_user.id))
            flash("رمز عبور با موفقیت تغییر کرد.", "success")
            return redirect(url_for("dashboard"))
        except Exception as e:
            flash(f"خطا در تغییر رمز عبور: {str(e)}", "danger")

    return render_template("change_password.html")

@app.route("/profile")
@login_required
def profile():
    emp_id = int(getattr(current_user, "id"))
    employee = db.get_employee_by_id(emp_id)
    return render_template("profile.html", employee=employee)

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500


@app.route("/404")
def page_404():
    return render_template("404.html"), 404


@app.route("/500")
def page_500():
    return render_template("500.html"), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port, debug=True)
