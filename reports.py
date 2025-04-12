import os
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

current_date_time = datetime.now()
formatted_date_time = current_date_time.strftime("%Y-%m-%d %H:%M:%S")


def create_long_form_roster_tex():
    """
    Creates and writes a LaTeX file named 'lfr.tex' to the 'files_roster_reports' directory.
    """

    # Define the file path (directory + file name)
    header_file_path = "files_roster_reports/lfrHeader.txt"
    output_file_path = "files_roster_reports/lfr.tex"

    # Step 1: Read the entire header file content into a list of lines
    with open(header_file_path, "r") as header_file:
        header_lines = header_file.readlines()

    # Step 2: Replace the token "current" with `formatted_date_time`
    if len(header_lines) >= 11:  # Ensure there are at least 11 lines
        header_lines[10] = header_lines[10].replace("current", formatted_date_time)

    # Step 3: Join the updated header lines into a single string
    header_content = ''.join(header_lines)

    # Step 4: Define placeholders for body and footer
    body_content = "% TODO: Add body content here\n"

    # Step 5: Concatenate the LaTeX content
    latex_content = header_content + "\n" + body_content + "\n\\end{document}"

    # Write the complete LaTeX content to the file
    with open(output_file_path, "w") as latex_file:
        latex_file.write(latex_content)

    print(f"The file 'lfr.tex' has been created in the 'files_roster_reports' directory.")


def fetch_records_from_view(view_name):
    """
    Fetches all records from a database view.

    Args:
        view_name (str): The name of the database view to query.

    Returns:
        list[dict]: A list of dictionaries, where each dictionary represents a record.
    """
    # Initialize database connection (replace with correct URI)
    DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///instance/clerk.sqlite3")
    engine = create_engine(DATABASE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Use the text() function to create a properly typed SQL query
        query = text(f"SELECT * FROM {view_name} ORDER BY name, office_precedence, first, last")

        # Execute the query and fetch all results as dictionaries
        result = session.execute(query).mappings().all()

        # 'result' is now a list of dictionaries
        records = [dict(row) for row in result]

        return records

    except Exception as e:
        print(f"An error occurred: {e}")
        return []

    finally:
        session.close()




if __name__ == "__main__":
    # create_long_form_roster_tex()
    records = fetch_records_from_view("report_record")
    for record in records:
        print(f"Column1: {record['first']}, Column2: {record['last']}")
