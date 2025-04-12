# routes/report.py

from flask import Blueprint, send_file
from models.report_record import ReportRecord
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import subprocess
import os
from collections import defaultdict

# Define the blueprint for all report-related routes
report_bp = Blueprint("report", __name__, url_prefix="/report")


@report_bp.route("/long")
def long_form_roster():
    from datetime import datetime
    from collections import defaultdict
    import os

    # Define absolute path to report folder
    basedir = os.path.abspath(os.path.dirname(__file__))
    report_dir = os.path.abspath(os.path.join(basedir, "..", "files_roster_reports"))

    tex_filename = "long_form_roster.tex"
    pdf_filename = "long_form_roster.pdf"
    tex_path = os.path.join(report_dir, tex_filename)
    pdf_path = os.path.join(report_dir, pdf_filename)

    # Step 1: Query and sort all records
    records = ReportRecord.query.order_by(
        ReportRecord.body_precedence,
        ReportRecord.office_precedence
    ).all()

    # Step 2: Group by body name
    grouped = defaultdict(list)
    for r in records:
        grouped[r.name].append(r)

    # Step 3: Render LaTeX using Jinja2
    env = Environment(
        loader=FileSystemLoader(report_dir),
        block_start_string='\\BLOCK{', block_end_string='}',
        variable_start_string='\\VAR{', variable_end_string='}',
        comment_start_string='\\%{', comment_end_string='}',
        autoescape=False
    )

    template = env.get_template("lfr_template.tex")
    rendered_tex = template.render(
        generated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        title="Long Form Roster",
        grouped=grouped
    )

    # Step 4: Write .tex file
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(rendered_tex)

    # Step 5: Clean up previous logs (optional safety)
    for ext in [".aux", ".log", ".synctex.gz"]:
        try:
            os.remove(os.path.join(report_dir, f"long_form_roster{ext}"))
        except FileNotFoundError:
            pass

    # Step 6: Compile with xelatex using absolute path
    result = subprocess.run(
        ["xelatex", "-interaction=nonstopmode", "-output-directory", report_dir, tex_path],
        cwd=report_dir,
        capture_output=True,
        text=True
    )

    if not os.path.exists(pdf_path):
        return (
            f"PDF not found.\n\n"
            f"LaTeX stdout:\n{result.stdout}\n\n"
            f"LaTeX stderr:\n{result.stderr}",
            500
        )

    return send_file(pdf_path, mimetype='application/pdf')


@report_bp.route("/short")
def short_form_roster():
    from datetime import datetime
    from collections import defaultdict
    import os

    # Define absolute path to report folder
    basedir = os.path.abspath(os.path.dirname(__file__))
    report_dir = os.path.abspath(os.path.join(basedir, "..", "files_roster_reports"))

    tex_filename = "short_form_roster.tex"
    pdf_filename = "short_form_roster.pdf"
    tex_path = os.path.join(report_dir, tex_filename)
    pdf_path = os.path.join(report_dir, pdf_filename)

    # Step 1: Query and sort all records
    records = ReportRecord.query.order_by(
        ReportRecord.body_precedence,
        ReportRecord.office_precedence
    ).all()

    # Step 2: Group by body name
    grouped = defaultdict(list)
    for r in records:
        grouped[r.name].append(r)

    # Step 3: Render LaTeX using Jinja2
    env = Environment(
        loader=FileSystemLoader(report_dir),
        block_start_string='\\BLOCK{', block_end_string='}',
        variable_start_string='\\VAR{', variable_end_string='}',
        comment_start_string='\\%{', comment_end_string='}',
        autoescape=False
    )

    template = env.get_template("sfr_template.tex")
    rendered_tex = template.render(
        generated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        title="Short Form Roster",
        grouped=grouped
    )

    # Step 4: Write the LaTeX source
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(rendered_tex)

    # Step 5: Clean up old auxiliary files
    for ext in [".aux", ".log", ".synctex.gz"]:
        try:
            os.remove(os.path.join(report_dir, f"short_form_roster{ext}"))
        except FileNotFoundError:
            pass

    # Step 6: Compile to PDF
    result = subprocess.run(
        ["xelatex", "-interaction=nonstopmode", "-output-directory", report_dir, tex_path],
        cwd=report_dir,
        capture_output=True,
        text=True
    )

    if not os.path.exists(pdf_path):
        return (
            f"PDF not found.\n\n"
            f"LaTeX stdout:\n{result.stdout}\n\n"
            f"LaTeX stderr:\n{result.stderr}",
            500
        )

    return send_file(pdf_path, mimetype='application/pdf')


@report_bp.route("/expirations")
def expirations_report():
    from datetime import datetime
    from collections import defaultdict
    import os

    # Absolute paths
    basedir = os.path.abspath(os.path.dirname(__file__))
    report_dir = os.path.abspath(os.path.join(basedir, "..", "files_roster_reports"))

    tex_filename = "expirations_report.tex"
    pdf_filename = "expirations_report.pdf"
    tex_path = os.path.join(report_dir, tex_filename)
    pdf_path = os.path.join(report_dir, pdf_filename)

    # Determine current year for filter and title
    current_year = datetime.now().year

    # Step 1: Filter by terms expiring this year
    records = ReportRecord.query.filter(
        ReportRecord.end.between(f"{current_year}-01-01", f"{current_year}-12-31")
    ).order_by(
        ReportRecord.body_precedence,
        ReportRecord.office_precedence
    ).all()

    # Step 2: Group and format end date
    grouped = defaultdict(list)
    for r in records:
        r.formatted_end = r.end.strftime("%Y-%m-%d") if r.end else ""
        grouped[r.name].append(r)

    # Step 3: Render LaTeX via Jinja2
    env = Environment(
        loader=FileSystemLoader(report_dir),
        block_start_string='\\BLOCK{', block_end_string='}',
        variable_start_string='\\VAR{', variable_end_string='}',
        comment_start_string='\\%{', comment_end_string='}',
        autoescape=False
    )

    template = env.get_template("expirations_template.tex")
    rendered_tex = template.render(
        generated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        title=f"Expirations — {current_year}",
        grouped=grouped
    )

    # Step 4: Write LaTeX file
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(rendered_tex)

    # Step 5: Clean up old temp files
    for ext in [".aux", ".log", ".synctex.gz"]:
        try:
            os.remove(os.path.join(report_dir, f"expirations_report{ext}"))
        except FileNotFoundError:
            pass

    # Step 6: Compile with xelatex
    result = subprocess.run(
        ["xelatex", "-interaction=nonstopmode", "-output-directory", report_dir, tex_path],
        cwd=report_dir,
        capture_output=True,
        text=True
    )

    if not os.path.exists(pdf_path):
        return (
            f"PDF not found.\n\n"
            f"LaTeX stdout:\n{result.stdout}\n\n"
            f"LaTeX stderr:\n{result.stderr}",
            500
        )

    return send_file(pdf_path, mimetype='application/pdf')


@report_bp.route("/vacancies")
def vacancies_report():
    from datetime import datetime
    from collections import defaultdict
    import os

    # Define absolute paths for robustness
    basedir = os.path.abspath(os.path.dirname(__file__))
    report_dir = os.path.abspath(os.path.join(basedir, "..", "files_roster_reports"))

    tex_filename = "vacancies_report.tex"
    pdf_filename = "vacancies_report.pdf"
    tex_path = os.path.join(report_dir, tex_filename)
    pdf_path = os.path.join(report_dir, pdf_filename)

    # Query and sort all records
    records = ReportRecord.query.order_by(
        ReportRecord.body_precedence,
        ReportRecord.office_precedence
    ).all()

    # Group by body and tag vacancies
    grouped = defaultdict(list)
    for r in records:
        is_vacant = (r.first and r.first.startswith("(Vacancy") and r.last == " ")
        full_name = r.first if is_vacant else f"{r.first or ''} {r.last or ''}".strip()

        r.is_vacant = is_vacant
        r.incumbent_display = full_name
        grouped[r.name].append(r)

    # Render LaTeX via Jinja2
    env = Environment(
        loader=FileSystemLoader(report_dir),
        block_start_string='\\BLOCK{', block_end_string='}',
        variable_start_string='\\VAR{', variable_end_string='}',
        comment_start_string='\\%{', comment_end_string='}',
        autoescape=False
    )

    template = env.get_template("vacancies_template.tex")
    rendered_tex = template.render(
        generated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        title="Vacancies and Appointments",
        grouped=grouped
    )

    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(rendered_tex)

    # Clean old log-related files just in case
    for ext in [".aux", ".log", ".synctex.gz"]:
        try:
            os.remove(os.path.join(report_dir, f"vacancies_report{ext}"))
        except FileNotFoundError:
            pass

    # Compile LaTeX
    result = subprocess.run(
        ["xelatex", "-interaction=nonstopmode", "-output-directory", report_dir, tex_path],
        cwd=report_dir,
        capture_output=True,
        text=True
    )

    if not os.path.exists(pdf_path):
        return (
            f"PDF not found.\n\n"
            f"LaTeX stdout:\n{result.stdout}\n\n"
            f"LaTeX stderr:\n{result.stderr}",
            500
        )

    return send_file(pdf_path, mimetype='application/pdf')

# @report_bp.route("/testvacancies")
# def test_vacancies_demo():
#     from datetime import datetime
#     from collections import defaultdict
#
#     # Simulated test data
#     class FakeRecord:
#         def __init__(self, body, title, first, last):
#             self.name = body
#             self.title = title
#             self.first = first
#             self.last = last
#             self.body_precedence = 1
#             self.office_precedence = 1
#
#             self.is_vacant = first.startswith("(Vacancy") and last == " "
#             self.incumbent_display = first if self.is_vacant else f"{first} {last}"
#
#     records = [
#         FakeRecord("Finance", "Chair", "Nancy", "Burke"),
#         FakeRecord("Finance", "Vice Chair", "(Vacancy 1)", " "),
#         FakeRecord("Dining", "Member", "Gerry", "Buckley"),
#         FakeRecord("Dining", "Member", "(Vacant)", " "),
#     ]
#
#     grouped = defaultdict(list)
#     for r in records:
#         grouped[r.name].append(r)
#
#     # Render using the actual vacancies template
#     env = Environment(
#         loader=FileSystemLoader("files_roster_reports"),
#         block_start_string='\\BLOCK{', block_end_string='}',
#         variable_start_string='\\VAR{', variable_end_string='}',
#         comment_start_string='\\%{', comment_end_string='}',
#         autoescape=False
#     )
#
#     template = env.get_template("vacancies_template.tex")
#     rendered_tex = template.render(
#         generated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#         title="Vacancies Test Output",
#         grouped=grouped
#     )
#
#     basedir = os.path.abspath(os.path.dirname(__file__))
#     report_dir = os.path.join(basedir, "..", "files_roster_reports")
#     report_dir = os.path.abspath(report_dir)
#
#     tex_filename = "vacancies_test.tex"
#     tex_path = os.path.join(report_dir, tex_filename)
#     with open(tex_path, "w", encoding="utf-8") as f:
#         f.write(rendered_tex)
#
#     result = subprocess.run(
#         ["xelatex", "-interaction=nonstopmode", "-output-directory", report_dir, tex_path],
#         cwd=report_dir,
#         capture_output=True,
#         text=True
#     )
#
#     cleanup_exts = [".aux", ".log", ".synctex.gz"]
#     for ext in cleanup_exts:
#         try:
#             os.remove(os.path.join("files_roster_reports", f"vacancies_test{ext}"))
#         except FileNotFoundError:
#             pass
#
#     pdf_path = os.path.join("files_roster_reports", "vacancies_test.pdf")
#     if not os.path.exists(pdf_path):
#         return (
#             f"PDF not found.\n\n"
#             f"LaTeX stdout:\n{result.stdout}\n\n"
#             f"LaTeX stderr:\n{result.stderr}",
#             500
#         )
#
#     return send_file(pdf_path, mimetype='application/pdf')
