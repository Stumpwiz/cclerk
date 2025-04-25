# routes/report.py

from flask import Blueprint, current_app
from models.report_record import ReportRecord
from jinja2 import Environment, FileSystemLoader
import subprocess

# Define the blueprint for all report-related routes
report_bp = Blueprint("report", __name__, url_prefix="/report")


@report_bp.route("/long")
def long_form_roster():
    from datetime import datetime
    from collections import defaultdict
    import os
    from flask import jsonify

    # Define the absolute path to the report folder
    basedir = os.path.abspath(os.path.dirname(__file__))
    report_dir = os.path.abspath(os.path.join(basedir, "..", "files_roster_reports"))


    tex_filename = "long_form_roster.tex"
    pdf_filename = "long_form_roster.pdf"
    tex_path = os.path.join(current_app.root_path, report_dir, tex_filename)
    pdf_path = os.path.join(current_app.root_path, report_dir, pdf_filename)

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

    # Step 4: Write the .tex file
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(rendered_tex)

    # Step 5: Clean up previous logs (optional safety)
    for ext in [".aux", ".log", ".synctex.gz"]:
        try:
            os.remove(os.path.join(report_dir, f"long_form_roster{ext}"))
        except FileNotFoundError:
            pass

    # Step 6: Compile with xelatex using the absolute path
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

    # Step 7: Clean up intermediate files
    for ext in [".aux", ".log"]:
        try:
            os.remove(os.path.join(report_dir, f"long_form_roster{ext}"))
        except FileNotFoundError:
            pass

    # Return JSON response with the filename
    return jsonify({"success": True, "filename": pdf_filename})


@report_bp.route("/short")
def short_form_roster():
    from datetime import datetime
    from collections import defaultdict
    import os
    from flask import jsonify

    # Define the absolute path to the report folder
    basedir = os.path.abspath(os.path.dirname(__file__))
    report_dir = os.path.abspath(os.path.join(basedir, "..", "files_roster_reports"))


    tex_filename = "short_form_roster.tex"
    pdf_filename = "short_form_roster.pdf"
    tex_path = os.path.join(current_app.root_path, report_dir, tex_filename)
    pdf_path = os.path.join(current_app.root_path, report_dir, pdf_filename)

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

    # Step 7: Clean up intermediate files
    for ext in [".aux", ".log"]:
        try:
            os.remove(os.path.join(report_dir, f"short_form_roster{ext}"))
        except FileNotFoundError:
            pass

    # Return JSON response with the filename
    return jsonify({"success": True, "filename": pdf_filename})


@report_bp.route("/expirations")
def expirations_report():
    from datetime import datetime
    from collections import defaultdict
    import os
    from flask import jsonify

    # Absolute paths
    basedir = os.path.abspath(os.path.dirname(__file__))
    report_dir = os.path.abspath(os.path.join(basedir, "..", "files_roster_reports"))


    tex_filename = "expirations_report.tex"
    pdf_filename = "expirations_report.pdf"
    tex_path = os.path.join(current_app.root_path, report_dir, tex_filename)
    pdf_path = os.path.join(current_app.root_path, report_dir, pdf_filename)

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

    # Step 4: Write the LaTeX file
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

    # Step 7: Clean up intermediate files
    for ext in [".aux", ".log"]:
        try:
            os.remove(os.path.join(report_dir, f"expirations_report{ext}"))
        except FileNotFoundError:
            pass

    # Return JSON response with the filename
    return jsonify({"success": True, "filename": pdf_filename})


@report_bp.route("/vacancies")
def vacancies_report():
    from datetime import datetime
    from collections import defaultdict
    import os
    from flask import jsonify

    # Define absolute paths for robustness
    basedir = os.path.abspath(os.path.dirname(__file__))
    report_dir = os.path.abspath(os.path.join(basedir, "..", "files_roster_reports"))


    tex_filename = "vacancies_report.tex"
    pdf_filename = "vacancies_report.pdf"
    tex_path = os.path.join(current_app.root_path, report_dir, tex_filename)
    pdf_path = os.path.join(current_app.root_path, report_dir, pdf_filename)

    # Query and sort all records
    records = ReportRecord.query.filter(
        ReportRecord.first.like('(Vacan%')
    ).order_by(
        ReportRecord.body_precedence,
        ReportRecord.office_precedence
    ).all()

    # Group by body and tag vacancies
    grouped = defaultdict(list)
    for r in records:
        is_vacant = (r.first and r.first.startswith("(Vacan") and r.last == " ")
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
        title="Vacancies",
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

    # Step 7: Clean up intermediate files
    for ext in [".aux", ".log"]:
        try:
            os.remove(os.path.join(report_dir, f"vacancies_report{ext}"))
        except FileNotFoundError:
            pass

    # Return JSON response with the filename
    return jsonify({"success": True, "filename": pdf_filename})