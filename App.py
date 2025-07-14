from flask import Flask, request, render_template
import pyodbc
import os
from werkzeug.utils import secure_filename
from waitress import serve  # Add waitress for production

app = Flask(__name__)

# === Configuration ===
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'png'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# SQL Server connection string
conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=192.168.1.27;"
    "DATABASE=CELIO_ETLDB;"
    "UID=sa;"
    "PWD=sa@1234#;"
)

# === Utility function to validate file ===
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# === Routes ===
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form['name']
            compliance_type = request.form['complianceType']
            sub_category = request.form.get('subCompliance', '')
            due_date = request.form['dueDate']
            payment_date = request.form['paymentDate']
            due_amount = float(request.form['dueAmount'])
            paid_amount = float(request.form['paidAmount'])
            balance_amount = float(request.form['balanceAmount'])
            remark = request.form['remark']
            document = request.files['document']

            # Save uploaded file
            document_path = ''
            if document and allowed_file(document.filename):
                filename = secure_filename(document.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                document.save(file_path)
                document_path = file_path

            # Insert data into SQL Server
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO dbo.CompliancePaymentTracker
                (Name, ComplianceType, SubCategory, DueDate, PaymentDate, DueAmount, PaidAmount, Remark, DocumentPath)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, compliance_type, sub_category, due_date, payment_date,
                  due_amount, paid_amount, remark, document_path))
            conn.commit()
            conn.close()

            return "Form submitted successfully!"

        except Exception as e:
            return f"Error submitting form: {str(e)}"

    return render_template('form.html')

# === Production Server ===
if __name__ == '__main__':
    # Use waitress instead of app.run()
    serve(app, host="0.0.0.0", port=8080)
