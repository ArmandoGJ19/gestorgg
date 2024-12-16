from database.conectiondb import transactions, category, users
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from bson import ObjectId
from utilities.common import convert_objectid_to_str
import urllib.parse
import json
from decouple import config
import pandas as pd
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors

EMAIL = config('EMAIL')
PASSWORD_GMAIL = config('PASSWORD_GMAIL')


def get_user(user_id):
    return users.find_one({"_id": ObjectId(user_id)})


def get_all_users():
    return users.find({"send_reports": True})


def get_date_range():
    end_date = datetime.now().replace(day=1)
    start_date = (end_date - timedelta(days=1)).replace(day=1)
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')


def get_transactions(user_id, start_date_str, end_date_str):
    return transactions.find(
        {"user_id": convert_objectid_to_str(user_id), "fecha": {"$gte": start_date_str, "$lte": end_date_str}})


def process_transactions(transactions_search):
    total_ingresos = 0
    total_gastos = 0
    table_rows = []
    table_html_rows = ""

    for transaction in transactions_search:
        category_name = category.find_one({"_id": ObjectId(transaction["category_id"])})
        monto = transaction["monto"]
        transaction_date = datetime.strptime(transaction["fecha"], '%Y-%m-%d') if isinstance(transaction["fecha"],
                                                                                             str) else transaction[
            "fecha"]

        if transaction["type"] == "ingreso":
            total_ingresos += monto
        else:
            total_gastos += monto

        table_html_rows += f"""
        <tr>
            <td>{transaction_date.strftime('%Y-%m-%d')}</td>
            <td>{transaction['descripcion']}</td>
            <td>{monto}</td>
            <td>{category_name['category_name']}</td>
        </tr>
        """

        table_rows.append([
            transaction_date.strftime('%Y-%m-%d'),
            transaction['descripcion'],
            monto,
            category_name['category_name']
        ])

    balance = total_ingresos - total_gastos
    return total_ingresos, total_gastos, balance, table_html_rows, table_rows


def generate_chart_url(total_ingresos, total_gastos, balance):
    chart_data = {
        "type": "bar",
        "data": {
            "labels": ["Ingresos", "Gastos", "Balance"],
            "datasets": [{
                "label": "Montos en $",
                "data": [total_ingresos, total_gastos, balance],
                "backgroundColor": [
                    "rgba(75, 192, 192, 0.2)",
                    "rgba(255, 99, 132, 0.2)",
                    "rgba(54, 162, 235, 0.2)"
                ],
                "borderColor": [
                    "rgba(75, 192, 192, 1)",
                    "rgba(255, 99, 132, 1)",
                    "rgba(54, 162, 235, 1)"
                ],
                "borderWidth": 1
            }]
        },
        "options": {
            "scales": {
                "y": {
                    "beginAtZero": True
                }
            }
        }
    }
    return f"https://quickchart.io/chart?c={urllib.parse.quote(json.dumps(chart_data))}"


def generate_report_html(user, total_ingresos, total_gastos, balance, table_rows):
    chart_url = generate_chart_url(total_ingresos, total_gastos, balance)
    return f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
            }}
            h2 {{
                color: #333;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            table, th, td {{
                border: 1px solid #ccc;
            }}
            th, td {{
                padding: 10px;
                text-align: left;
            }}
            th {{
                background-color: #f4f4f4;
            }}
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
        </style>
    </head>
    <body>
        <h2>Reporte mensual de {user['name']} {user['lastname']} ({user['email']})</h2>
        <table>
            <tr>
                <th>Fecha</th>
                <th>Descripción</th>
                <th>Monto</th>
                <th>Tipo de gasto</th>
            </tr>
            {table_rows}
        </table>
        <img src="{chart_url}" alt="Gráfico de Ingresos, Gastos y Balance">
        <div>
        <table><tr>
        <td>Total Ingresos:</td>
        <td>${total_ingresos}</td>
        </tr>
        <tr>
        <td>Total Gastos:</td>
        <td>${total_gastos}</td>
        </tr>
        <tr>
        <td>Balance:</td>
        <td>${balance}</td>
        </tr>
        </table>
        </div>
    </body>
    </html>
    """


def generate_excel(table_rows):
    df = pd.DataFrame(table_rows, columns=["Fecha", "Descripción", "Monto", "Tipo de gasto"])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Reporte')
    return output.getvalue()


def generate_pdf(user, total_ingresos, total_gastos, balance, table_rows):
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter)
    elements = []

    title = f"Reporte mensual de {user['name']} {user['lastname']}"
    elements.append(Paragraph(title, get_sample_style_sheet()['Title']))

    user_info = f"Nombre: {user['name']} {user['lastname']}<br/>Email: {user['email']}"
    elements.append(Paragraph(user_info, get_sample_style_sheet()['Normal']))

    summary_data = [
        ["Total Ingresos", f"${total_ingresos}"],
        ["Total Gastos", f"${total_gastos}"],
        ["Balance", f"${balance}"]
    ]
    summary_table = Table(summary_data, colWidths=[150, 100])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(summary_table)

    elements.append(Paragraph("<br/><br/>", get_sample_style_sheet()['Normal']))

    table_data = [["Fecha", "Descripción", "Monto", "Tipo de gasto"]] + table_rows
    transactions_table = Table(table_data)
    transactions_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(transactions_table)

    doc.build(elements)
    return output.getvalue()


def get_sample_style_sheet():
    from reportlab.lib.styles import getSampleStyleSheet
    return getSampleStyleSheet()


def send_email(email_to: str, subject: str, html_content: str, attachments: list):
    sender = EMAIL
    password = PASSWORD_GMAIL
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender, password)

    message = MIMEMultipart()
    message['From'] = sender
    message['To'] = email_to
    message['Subject'] = subject

    message.attach(MIMEText(html_content, "html"))

    for attachment in attachments:
        message.attach(attachment)

    server.sendmail(sender, email_to, message.as_string())
    server.quit()


def generate_and_send_reports():
    start_date_str, end_date_str = get_date_range()
    all_users = get_all_users()

    for user in all_users:
        transactions_search = get_transactions(user["_id"], start_date_str, end_date_str)
        total_ingresos, total_gastos, balance, table_html_rows, table_rows = process_transactions(transactions_search)

        if not table_rows:
            no_transactions_html = f"""
            <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                    }}
                    h2 {{
                        color: #333;
                    }}
                </style>
            </head>
            <body>
                <h2>Reporte mensual de {user['name']} {user['lastname']} ({user['email']})</h2>
                <p>No hubo ingresos ni gastos en el periodo.</p>
            </body>
            </html>
            """
            send_email(user["email"], "Reporte Mensual", no_transactions_html, [])
        else:
            report_html = generate_report_html(user, total_ingresos, total_gastos, balance, table_html_rows)
            excel_data = generate_excel(table_rows)
            pdf_data = generate_pdf(user, total_ingresos, total_gastos, balance, table_rows)

            attachments = [
                MIMEApplication(excel_data, Name="reporte.xlsx"),
                MIMEApplication(pdf_data, Name="reporte.pdf")
            ]
            for attachment in attachments:
                attachment['Content-Disposition'] = f'attachment; filename="{attachment.get_filename()}"'

            send_email(user["email"], "Reporte Mensual", report_html, attachments)
