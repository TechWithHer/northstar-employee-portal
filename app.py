from flask import Flask, request, redirect, render_template
import pymysql
import boto3
import json


app = Flask(__name__)


# =========================================================
# DATABASE CONNECTION
# Credentials retrieved from AWS Secrets Manager
# House EC2 authenticates using Northstar-House-App-Role
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

    # No employee searched yet
    if not employee_id:
        return render_template("home.html")

    # Employee ID exists, so connect to database
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

    # Employee does not exist
    if not employee:

        return f"""
        <h1>Northstar Employee Records Portal</h1>

        <h2>Employee {employee_id} not found.</h2>

        <a href="/">Search Again</a>

        <br><br>

        <a href="/employees">View All Employees</a>
        """

    # Employee found
    return f"""
    <h1>Northstar Employee Records Portal</h1>

    <h2>Employee Details</h2>

    <p><strong>Employee ID:</strong> {employee[0]}</p>
    <p><strong>Name:</strong> {employee[1]}</p>
    <p><strong>Email:</strong> {employee[2]}</p>
    <p><strong>Phone:</strong> {employee[3]}</p>
    <p><strong>Department:</strong> {employee[4]}</p>
    <p><strong>Job Role:</strong> {employee[5]}</p>
    <p><strong>Location:</strong> {employee[6]}</p>
    <p><strong>Status:</strong> {employee[7]}</p>
    <p><strong>Joining Date:</strong> {employee[8]}</p>

    <br>

    <a href="/edit/{employee[0]}">Edit Employee</a>

    <br><br>

    <a href="/">Search Another Employee</a>

    <br><br>

    <a href="/employees">View All Employees</a>
    """


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

    rows = ""

    for employee in employee_list:

        rows += f"""
        <tr>

            <td>{employee[0]}</td>
            <td>{employee[1]}</td>
            <td>{employee[2]}</td>
            <td>{employee[3]}</td>
            <td>{employee[4]}</td>

            <td>
                <a href="/?employee_id={employee[0]}">View</a>
                |
                <a href="/edit/{employee[0]}">Edit</a>
                |
                <a href="/delete/{employee[0]}">Delete</a>
            </td>

        </tr>
        """

    return f"""
    <h1>Northstar Employee Records Portal</h1>

    <h2>Employees</h2>

    <a href="/">Search Employee</a>
    |
    <a href="/add">Add Employee</a>

    <br><br>

    <table border="1" cellpadding="8">

        <tr>
            <th>Employee ID</th>
            <th>Name</th>
            <th>Department</th>
            <th>Job Role</th>
            <th>Status</th>
            <th>Actions</th>
        </tr>

        {rows}

    </table>
    """


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

    return """
    <h1>Northstar Employee Records Portal</h1>

    <h2>Add Employee</h2>

    <form method="POST">

        Employee ID:
        <input type="number" name="employee_id" required>
        <br><br>

        Full Name:
        <input type="text" name="full_name" required>
        <br><br>

        Email:
        <input type="email" name="email" required>
        <br><br>

        Phone:
        <input type="text" name="phone">
        <br><br>

        Department:
        <input type="text" name="department">
        <br><br>

        Job Role:
        <input type="text" name="job_role">
        <br><br>

        Location:
        <input type="text" name="location">
        <br><br>

        Employment Status:

        <select name="employment_status">
            <option value="Active">Active</option>
            <option value="Inactive">Inactive</option>
        </select>

        <br><br>

        Joining Date:
        <input type="date" name="joining_date">

        <br><br>

        <button type="submit">
            Add Employee
        </button>

    </form>

    <br>

    <a href="/employees">
        Back to Employees
    </a>
    """


# =========================================================
# EDIT EMPLOYEE
# =========================================================

@app.route("/edit/<int:employee_id>", methods=["GET", "POST"])
def edit_employee(employee_id):

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            # -------------------------
            # UPDATE EMPLOYEE
            # -------------------------

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

            # -------------------------
            # LOAD EMPLOYEE
            # -------------------------

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

        return """
        <h2>Employee not found.</h2>

        <a href="/employees">
            Back to Employees
        </a>
        """

    active_selected = (
        "selected"
        if employee[7] == "Active"
        else ""
    )

    inactive_selected = (
        "selected"
        if employee[7] == "Inactive"
        else ""
    )

    return f"""
    <h1>Northstar Employee Records Portal</h1>

    <h2>Edit Employee {employee[0]}</h2>

    <form method="POST">

        Full Name:
        <input
            type="text"
            name="full_name"
            value="{employee[1]}"
            required
        >

        <br><br>

        Email:
        <input
            type="email"
            name="email"
            value="{employee[2]}"
            required
        >

        <br><br>

        Phone:
        <input
            type="text"
            name="phone"
            value="{employee[3] or ''}"
        >

        <br><br>

        Department:
        <input
            type="text"
            name="department"
            value="{employee[4] or ''}"
        >

        <br><br>

        Job Role:
        <input
            type="text"
            name="job_role"
            value="{employee[5] or ''}"
        >

        <br><br>

        Location:
        <input
            type="text"
            name="location"
            value="{employee[6] or ''}"
        >

        <br><br>

        Employment Status:

        <select name="employment_status">

            <option
                value="Active"
                {active_selected}
            >
                Active
            </option>

            <option
                value="Inactive"
                {inactive_selected}
            >
                Inactive
            </option>

        </select>

        <br><br>

        Joining Date:

        <input
            type="date"
            name="joining_date"
            value="{employee[8] or ''}"
        >

        <br><br>

        <button type="submit">
            Update Employee
        </button>

    </form>

    <br>

    <a href="/?employee_id={employee[0]}">
        Cancel
    </a>
    """


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

                return """
                <h2>Employee not found.</h2>

                <a href="/employees">
                    Back to Employees
                </a>
                """

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

    return f"""
    <h1>Northstar Employee Records Portal</h1>

    <h2>Delete Employee</h2>

    <p>
        Are you sure you want to delete
        <strong>{employee[1]}</strong>
        (Employee ID: {employee[0]})?
    </p>

    <form method="POST">

        <button type="submit">
            Yes, Delete Employee
        </button>

    </form>

    <br>

    <a href="/employees">
        Cancel
    </a>
    """


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000
    )