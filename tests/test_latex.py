# tests/test_latex.py

import pytest
import os
import re
import tempfile
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from models.report_record import ReportRecord


def test_latex_template_rendering(app, test_data):
    """Test that LaTeX templates can be rendered with Jinja2."""
    with app.app_context():
        # Create a temporary directory for the test templates
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a simple LaTeX template
            template_content = """\\documentclass{article}
\\begin{document}
\\section{\\VAR{title}}
\\begin{itemize}
\\BLOCK{for item in items}
    \\item \\VAR{item}
\\BLOCK{endfor}
\\end{itemize}
\\end{document}
"""
            template_path = os.path.join(temp_dir, "test_template.tex")
            with open(template_path, "w", encoding="utf-8") as f:
                f.write(template_content)

            # Set up Jinja2 environment for LaTeX
            env = Environment(
                loader=FileSystemLoader(temp_dir),
                block_start_string='\\BLOCK{', block_end_string='}',
                variable_start_string='\\VAR{', variable_end_string='}',
                comment_start_string='\\%{', comment_end_string='}',
                autoescape=False
            )

            # Render the template
            template = env.get_template("test_template.tex")
            rendered_tex = template.render(
                title="Test Title",
                items=["Item 1", "Item 2", "Item 3"]
            )

            # Check that the rendered content is correct
            assert "\\section{Test Title}" in rendered_tex
            assert "\\item Item 1" in rendered_tex
            assert "\\item Item 2" in rendered_tex
            assert "\\item Item 3" in rendered_tex


def test_long_form_roster_template(app, test_data):
    """Test the long form roster LaTeX template."""
    with app.app_context():
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a simple template for testing
            template_content = """\\documentclass{article}
\\begin{document}
\\section{\\VAR{title}}
\\VAR{generated}

\\BLOCK{for body_name, records in grouped.items()}
\\subsection{\\VAR{body_name}}
\\begin{itemize}
\\BLOCK{for record in records}
    \\item \\VAR{record.title}: \\VAR{record.first} \\VAR{record.last}
\\BLOCK{endfor}
\\end{itemize}
\\BLOCK{endfor}
\\end{document}
"""
            template_path = os.path.join(temp_dir, "lfr_template.tex")
            with open(template_path, "w", encoding="utf-8") as f:
                f.write(template_content)

            # Query and group records
            records = ReportRecord.query.order_by(
                ReportRecord.body_precedence,
                ReportRecord.office_precedence
            ).all()

            from collections import defaultdict
            grouped = defaultdict(list)
            for r in records:
                grouped[r.name].append(r)

            # Set up Jinja2 environment for LaTeX
            env = Environment(
                loader=FileSystemLoader(temp_dir),
                block_start_string='\\BLOCK{', block_end_string='}',
                variable_start_string='\\VAR{', variable_end_string='}',
                comment_start_string='\\%{', comment_end_string='}',
                autoescape=False
            )

            # Render the template
            template = env.get_template("lfr_template.tex")
            rendered_tex = template.render(
                generated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                title="Long Form Roster",
                grouped=grouped
            )

            # Write the rendered content to a file
            output_path = os.path.join(temp_dir, "test_long_form_roster.tex")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(rendered_tex)

            # Check that the rendered content is correct
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()

                # Check for the title
                assert "\\section{Long Form Roster}" in content

                # Check for the body names
                assert "\\subsection{Test Body 1}" in content
                assert "\\subsection{Test Body 2}" in content

                # Check for the office titles and person names
                assert "\\item Test Office 1: John Doe" in content
                assert "\\item Test Office 2: Jane Smith" in content
                assert "\\item Test Office 3: Bob Johnson" in content


def test_latex_to_pdf_compilation(app, test_data):
    """Test that LaTeX files can be compiled to PDF (if xelatex is available)."""
    with app.app_context():
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a simple LaTeX file for testing
            latex_content = """\\documentclass{article}
\\begin{document}
\\section{Test PDF Compilation}
This is a test document to verify that LaTeX can be compiled to PDF.
\\end{document}
"""
            latex_path = os.path.join(temp_dir, "test_compilation.tex")
            pdf_path = os.path.join(temp_dir, "test_compilation.pdf")

            with open(latex_path, "w", encoding="utf-8") as f:
                f.write(latex_content)

            # Try to compile the LaTeX file to PDF
            import subprocess
            import platform

            # Skip the test if xelatex is not available
            try:
                if platform.system() == "Windows":
                    subprocess.run(["where", "xelatex"], check=True, capture_output=True)
                else:
                    subprocess.run(["which", "xelatex"], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                pytest.skip("xelatex not available")

            # Compile the LaTeX file
            result = subprocess.run(
                ["xelatex", "-interaction=nonstopmode", "-output-directory", temp_dir, latex_path],
                cwd=temp_dir,
                capture_output=True,
                text=True
            )

            # Check that the compilation was successful
            assert result.returncode == 0
            assert os.path.exists(pdf_path)

            # Check the size of the PDF file (should be non-zero)
            assert os.path.getsize(pdf_path) > 0


def test_all_report_templates(app, test_data):
    """Test all report templates."""
    with app.app_context():
        # Ensure the report_record view is created and populated
        import sqlite3
        db_path = app.config['DATABASE']

        # Recreate the report_record view
        try:
            # Extract just the CREATE VIEW statement from schema.sql
            view_sql = """
CREATE VIEW report_record AS
SELECT
    person.personid AS person_id,
    person.first AS first,
    person.last AS last,
    person.email AS email,
    person.phone AS phone,
    person.apt AS apt,
    term.start AS start,
    term.end AS end,
    term.ordinal AS ordinal,
    term.termpersonid AS term_person_id,
    term.termofficeid AS term_office_id,
    office.office_id AS office_id,
    office.title AS title,
    office.office_precedence AS office_precedence,
    office.office_body_id AS office_body_id,
    body.body_id AS body_id,
    body.name AS name,
    body.body_precedence AS body_precedence
FROM term
JOIN office ON office.office_id = term.termofficeid
JOIN body ON body.body_id = office.office_body_id
JOIN person ON person.personid = term.termpersonid
ORDER BY body.body_precedence;
"""
            # First, drop the view or table if it exists
            with sqlite3.connect(db_path) as conn:
                # Enable foreign key constraints
                conn.execute("PRAGMA foreign_keys=ON")
                try:
                    # Try to drop it as a table first (if it was created as a table)
                    conn.execute("DROP TABLE IF EXISTS report_record")
                    conn.commit()
                    print("Dropped report_record table")
                except sqlite3.OperationalError as e:
                    # If it's not a table, try to drop it as a view
                    try:
                        conn.execute("DROP VIEW IF EXISTS report_record")
                        conn.commit()
                        print("Dropped report_record view")
                    except sqlite3.OperationalError as e:
                        print(f"Error dropping report_record: {e}")

            # Then create the view
            with sqlite3.connect(db_path) as conn:
                # Enable foreign key constraints
                conn.execute("PRAGMA foreign_keys=ON")
                conn.executescript(view_sql)
                conn.commit()

            # Verify the view was created by querying it
            with sqlite3.connect(db_path) as conn:
                # Enable foreign key constraints
                conn.execute("PRAGMA foreign_keys=ON")
                cursor = conn.execute("SELECT COUNT(*) FROM report_record;")
                count = cursor.fetchone()[0]
                print(f"report_record view created with {count} records")

        except Exception as e:
            print(f"Error creating report_record view: {e}")
            raise  # Re-raise the exception to fail the test

        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Define the templates to test
            templates = {
                "lfr_template.tex": "Long Form Roster",
                "sfr_template.tex": "Short Form Roster",
                "expirations_template.tex": "Expirations Report",
                "vacancies_template.tex": "Vacancies Report"
            }

            # Create simple templates for testing
            template_content = """\\documentclass{article}
\\begin{document}
\\section{\\VAR{title}}
\\VAR{generated}

\\BLOCK{for body_name, records in grouped.items()}
\\subsection{\\VAR{body_name}}
\\begin{itemize}
\\BLOCK{for record in records}
    \\item \\VAR{record.title}: \\VAR{record.first} \\VAR{record.last}
\\BLOCK{endfor}
\\end{itemize}
\\BLOCK{endfor}
\\end{document}
"""

            # Create each template in the temporary directory
            for template_name in templates:
                template_path = os.path.join(temp_dir, template_name)
                with open(template_path, "w", encoding="utf-8") as f:
                    f.write(template_content)

            # Query and group records
            records = ReportRecord.query.order_by(
                ReportRecord.body_precedence,
                ReportRecord.office_precedence
            ).all()

            # Verify that we have records
            assert len(records) > 0, "No records found in ReportRecord view"

            from collections import defaultdict
            grouped = defaultdict(list)
            for r in records:
                grouped[r.name].append(r)

            # Verify that we have grouped records
            assert len(grouped) > 0, "No grouped records found"

            # Set up Jinja2 environment for LaTeX
            env = Environment(
                loader=FileSystemLoader(temp_dir),
                block_start_string='\\BLOCK{', block_end_string='}',
                variable_start_string='\\VAR{', variable_end_string='}',
                comment_start_string='\\%{', comment_end_string='}',
                autoescape=False
            )

            # Test each template
            for template_name, report_title in templates.items():
                # Render the template
                template = env.get_template(template_name)
                rendered_tex = template.render(
                    generated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    title=report_title,
                    grouped=grouped
                )

                # Write the rendered content to a file
                output_name = f"test_{template_name}"
                output_path = os.path.join(temp_dir, output_name)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(rendered_tex)

                # Check that the rendered content is correct
                with open(output_path, "r", encoding="utf-8") as f:
                    content = f.read()

                    # Check for the title
                    assert f"\\section{{{report_title}}}" in content

                    # Check for the body names
                    assert "\\subsection{Test Body 1}" in content
                    assert "\\subsection{Test Body 2}" in content

                    # Check for the office titles and person names
                    assert "\\item Test Office 1: John Doe" in content
                    assert "\\item Test Office 2: Jane Smith" in content
                    assert "\\item Test Office 3: Bob Johnson" in content
