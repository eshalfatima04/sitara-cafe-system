from flask import Flask, render_template, redirect, url_for, request, session
import sqlite3
import datetime

app = Flask(__name__)
app.secret_key = "sitara_cafe_secret_key"


# Meal serving times (fixed info shown to employees)
meal_times = {
    "Breakfast": "7:00 AM – 9:00 AM",
    "Lunch":     "1:00 PM – 2:00 PM",
    "Dinner":    "7:00 PM – 9:00 PM",
}


# Helper: load the whole weekly menu from the database
def get_weekly_menu():
    connection = sqlite3.connect("cafe.db")
    cursor = connection.cursor()
    cursor.execute("SELECT day, breakfast, lunch, dinner FROM menu")
    rows = cursor.fetchall()
    connection.close()

    menu = {}
    for day, breakfast, lunch, dinner in rows:
        menu[day] = {"Breakfast": breakfast, "Lunch": lunch, "Dinner": dinner}
    return menu


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        connection = sqlite3.connect("cafe.db")
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM employees WHERE username = ? AND password = ?",
            (username, password)
        )
        employee = cursor.fetchone()
        connection.close()

        if employee:
            session["username"] = username
            session["full_name"] = employee[3]
            session["is_admin"] = employee[4]
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid username or password. Please try again.")

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))

    return render_template("dashboard.html", full_name=session["full_name"])


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/attendance")
def attendance():
    if "username" not in session:
        return redirect(url_for("login"))

    today = datetime.date.today().strftime("%Y-%m-%d")

    connection = sqlite3.connect("cafe.db")
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM attendance WHERE username = ? AND date = ?",
        (session["username"], today)
    )
    already = cursor.fetchone()
    connection.close()

    today_day = datetime.date.today().strftime("%A")
    todays_meal = get_weekly_menu().get(today_day)

    if already:
        return render_template(
            "attendance.html",
            full_name=session["full_name"],
            already_marked=True,
            previous_choice=already[5],
            previous_request=already[6],
            today_day=today_day,
            todays_meal=todays_meal,
            meal_times=meal_times
        )

    return render_template(
        "attendance.html",
        full_name=session["full_name"],
        today_day=today_day,
        todays_meal=todays_meal,
        meal_times=meal_times
    )


@app.route("/mark_attendance", methods=["POST"])
def mark_attendance():
    if "username" not in session:
        return redirect(url_for("login"))

    today = datetime.date.today().strftime("%Y-%m-%d")

    connection = sqlite3.connect("cafe.db")
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM attendance WHERE username = ? AND date = ?",
        (session["username"], today)
    )
    already = cursor.fetchone()

    today_day = datetime.date.today().strftime("%A")
    todays_meal = get_weekly_menu().get(today_day)

    if already:
        connection.close()
        return render_template(
            "attendance.html",
            full_name=session["full_name"],
            already_marked=True,
            previous_choice=already[5],
            previous_request=already[6],
            today_day=today_day,
            todays_meal=todays_meal,
            meal_times=meal_times
        )

    choice = request.form["choice"]
    meal_choice = "Will Eat" if choice == "yes" else "Not Eating"

    special_request = request.form.get("special_request", "").strip()
    if choice != "yes":
        special_request = ""

    cursor.execute(
        "INSERT INTO attendance (username, date, status, meal_choice, special_request) VALUES (?, ?, ?, ?, ?)",
        (session["username"], today, "Present", meal_choice, special_request)
    )
    connection.commit()
    connection.close()

    return render_template(
        "attendance.html",
        full_name=session["full_name"],
        marked=True,
        meal_choice=meal_choice,
        special_request=special_request,
        today_day=today_day,
        todays_meal=todays_meal,
        meal_times=meal_times
    )


@app.route("/attendance_records")
def attendance_records():
    if "username" not in session:
        return redirect(url_for("login"))
    if session.get("is_admin") != 1:
        return "Access denied. Only admins can view attendance records.", 403

    connection = sqlite3.connect("cafe.db")
    cursor = connection.cursor()
    cursor.execute("""
        SELECT attendance.id, employees.full_name, attendance.username,
               attendance.date, attendance.status, attendance.meal_choice,
               attendance.special_request
        FROM attendance
        LEFT JOIN employees ON attendance.username = employees.username
        ORDER BY attendance.id DESC
    """)
    records = cursor.fetchall()
    connection.close()

    return render_template("attendance_records.html", records=records)


@app.route("/kitchen_summary")
def kitchen_summary():
    if "username" not in session:
        return redirect(url_for("login"))
    if session.get("is_admin") != 1:
        return "Access denied. Only admins can view the kitchen summary.", 403

    today = datetime.date.today().strftime("%Y-%m-%d")
    today_day = datetime.date.today().strftime("%A")

    connection = sqlite3.connect("cafe.db")
    cursor = connection.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM attendance WHERE date = ? AND meal_choice = ?",
        (today, "Will Eat")
    )
    eating_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM attendance WHERE date = ? AND meal_choice = ?",
        (today, "Not Eating")
    )
    not_eating_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT employees.full_name, attendance.special_request
        FROM attendance
        LEFT JOIN employees ON attendance.username = employees.username
        WHERE attendance.date = ?
          AND attendance.meal_choice = 'Will Eat'
          AND attendance.special_request != ''
    """, (today,))
    requests = cursor.fetchall()

    connection.close()

    total_present = eating_count + not_eating_count

    return render_template(
        "kitchen_summary.html",
        today_day=today_day,
        today=today,
        eating_count=eating_count,
        not_eating_count=not_eating_count,
        total_present=total_present,
        requests=requests,
        todays_meal=get_weekly_menu().get(today_day),
        meal_times=meal_times
    )


@app.route("/edit_menu", methods=["GET", "POST"])
def edit_menu():
    if "username" not in session:
        return redirect(url_for("login"))
    if session.get("is_admin") != 1:
        return "Access denied. Only admins can edit the menu.", 403

    connection = sqlite3.connect("cafe.db")
    cursor = connection.cursor()

    if request.method == "POST":
        # Save each day's meals from the submitted form
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for day in days:
            breakfast = request.form.get(day + "_breakfast", "").strip()
            lunch = request.form.get(day + "_lunch", "").strip()
            dinner = request.form.get(day + "_dinner", "").strip()

            cursor.execute(
                "UPDATE menu SET breakfast = ?, lunch = ?, dinner = ? WHERE day = ?",
                (breakfast, lunch, dinner, day)
            )

        connection.commit()
        connection.close()
        return render_template("edit_menu.html", menu=get_weekly_menu(), success="Menu updated successfully!")

    connection.close()
    return render_template("edit_menu.html", menu=get_weekly_menu())


@app.route("/add_employee", methods=["GET", "POST"])
def add_employee():
    if "username" not in session:
        return redirect(url_for("login"))
    if session.get("is_admin") != 1:
        return "Access denied. Only admins can add employees.", 403

    if request.method == "POST":
        new_username = request.form["username"]
        new_password = request.form["password"]
        new_full_name = request.form["full_name"]
        new_is_admin = 1 if request.form.get("is_admin") == "yes" else 0

        connection = sqlite3.connect("cafe.db")
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM employees WHERE username = ?", (new_username,))
        existing = cursor.fetchone()

        if existing:
            connection.close()
            return render_template("add_employee.html", error="That username already exists. Choose another.")

        cursor.execute(
            "INSERT INTO employees (username, password, full_name, is_admin) VALUES (?, ?, ?, ?)",
            (new_username, new_password, new_full_name, new_is_admin)
        )
        connection.commit()
        connection.close()

        return render_template("add_employee.html", success=f"Employee '{new_full_name}' added successfully!")

    return render_template("add_employee.html")


@app.route("/menu")
def menu():
    if "username" not in session:
        return redirect(url_for("login"))

    return render_template("menu.html")


@app.route("/save_order", methods=["POST"])
def save_order():
    if "username" not in session:
        return redirect(url_for("login"))

    customer_name = request.form["customer_name"]
    tea = int(request.form["tea"])
    coffee = int(request.form["coffee"])
    sandwich = int(request.form["sandwich"])
    burger = int(request.form["burger"])

    total = (tea * 20) + (coffee * 40) + (sandwich * 60) + (burger * 80)

    connection = sqlite3.connect("cafe.db")
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO orders
        (customer_name, tea, coffee, sandwich, burger, total)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (customer_name, tea, coffee, sandwich, burger, total))

    connection.commit()
    connection.close()

    return redirect(url_for("orders"))


@app.route("/orders")
def orders():
    if "username" not in session:
        return redirect(url_for("login"))

    connection = sqlite3.connect("cafe.db")
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM orders ORDER BY id DESC")
    orders = cursor.fetchall()

    connection.close()

    return render_template("orders.html", orders=orders)


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)