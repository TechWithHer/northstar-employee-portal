from flask import Flask, request, redirect, render_template
import pymysql
import boto3
import json


app = Flask(__name__)


# =========================================================
# DATABASE CONNECTION
# AWS Secrets Manager + EC2 IAM Role
# =========================================================

def get_connection():

    secret_name = "northstar/prod/database"
    region_name = "ap-south-1"

    client = boto3.client(
        "secretsmanager",
        region_name=region_name
    )

    response = client.get_secret_value(
        SecretId=secret_name
    )

    secret = json.loads(response["SecretString"])

    return pymysql.connect(
        host=secret["host"],
        user=secret["username"],
        password=secret["password"],
        database=secret["database"]
    )


# =========================================================
# HOME / SEARCH EMPLOYEE
# =========================================================

@app.route("/")
def home():

    employee_id = request.args.get("employee_id")

    # User has not searched yet
    if not employee_id:
        return render_template(
            "home.html",
            employee=None,
            searched_id=None
        )

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    employee_id,
                    full_name,
                    email,
                    phone,
                    department,
                    job_role,
                    location,
                    employment_status,
                    joining_date
                FROM employees
                WHERE employee_id = %s
                """,
                (employee_id,)
            )

            employee = cursor.fetchone()

    finally:
        connection.close()

    return render_template(
        "home.html",
        employee=employee,
        searched_id=employee_id
    )


# =========================================================
# VIEW ALL EMPLOYEES
# =========================================================

@app.route("/employees")
def employees():

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    employee_id,
                    full_name,
                    department,
                    job_role,
                    employment_status
                FROM employees
                ORDER BY employee_id
                """
            )

            employee_list = cursor.fetchall()

    finally:
        connection.close()

    return render_template(
        "employees.html",
        employees=employee_list
    )


# =========================================================
# ADD EMPLOYEE
# =========================================================

@app.route("/add", methods=["GET", "POST"])
def add_employee():

    if request.method == "POST":

        employee_id = request.form["employee_id"]
        full_name = request.form["full_name"]
        email = request.form["email"]
        phone = request.form["phone"]
        department = request.form["department"]
        job_role = request.form["job_role"]
        location = request.form["location"]
        employment_status = request.form["employment_status"]
        joining_date = request.form["joining_date"]

        connection = get_connection()

        try:

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    INSERT INTO employees
                    (
                        employee_id,
                        full_name,
                        email,
                        phone,
                        department,
                        job_role,
                        location,
                        employment_status,
                        joining_date
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        employee_id,
                        full_name,
                        email,
                        phone,
                        department,
                        job_role,
                        location,
                        employment_status,
                        joining_date
                    )
                )

            connection.commit()

        finally:
            connection.close()

        return redirect("/employees")

    return render_template("add.html")


# =========================================================
# EDIT EMPLOYEE
# =========================================================

@app.route(
    "/edit/<int:employee_id>",
    methods=["GET", "POST"]
)
def edit_employee(employee_id):

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            # UPDATE EMPLOYEE
            if request.method == "POST":

                full_name = request.form["full_name"]
                email = request.form["email"]
                phone = request.form["phone"]
                department = request.form["department"]
                job_role = request.form["job_role"]
                location = request.form["location"]
                employment_status = request.form["employment_status"]
                joining_date = request.form["joining_date"]

                cursor.execute(
                    """
                    UPDATE employees
                    SET
                        full_name = %s,
                        email = %s,
                        phone = %s,
                        department = %s,
                        job_role = %s,
                        location = %s,
                        employment_status = %s,
                        joining_date = %s
                    WHERE employee_id = %s
                    """,
                    (
                        full_name,
                        email,
                        phone,
                        department,
                        job_role,
                        location,
                        employment_status,
                        joining_date,
                        employee_id
                    )
                )

                connection.commit()

                return redirect(
                    f"/?employee_id={employee_id}"
                )

            # LOAD EMPLOYEE
            cursor.execute(
                """
                SELECT
                    employee_id,
                    full_name,
                    email,
                    phone,
                    department,
                    job_role,
                    location,
                    employment_status,
                    joining_date
                FROM employees
                WHERE employee_id = %s
                """,
                (employee_id,)
            )

            employee = cursor.fetchone()

    finally:
        connection.close()

    if not employee:
        return redirect("/employees")

    return render_template(
        "edit.html",
        employee=employee
    )


# =========================================================
# DELETE EMPLOYEE
# =========================================================

@app.route(
    "/delete/<int:employee_id>",
    methods=["GET", "POST"]
)
def delete_employee(employee_id):

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    employee_id,
                    full_name
                FROM employees
                WHERE employee_id = %s
                """,
                (employee_id,)
            )

            employee = cursor.fetchone()

            if not employee:
                return redirect("/employees")

            if request.method == "POST":

                cursor.execute(
                    """
                    DELETE FROM employees
                    WHERE employee_id = %s
                    """,
                    (employee_id,)
                )

                connection.commit()

                return redirect("/employees")

    finally:
        connection.close()

    return render_template(
        "delete.html",
        employee=employee
    )


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000
    )