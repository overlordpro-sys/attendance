import PySimpleGUI as sg
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from read import readUID
PAGE_SIZE = 10  # Change this to whatever page size you want


# window to edit the user data associated with an rfid tag in the database
def confirm_window(user_id, mydb, cursor, first="", last="", team=""):
    window = sg.Window("Attendance", [[sg.Text("Is this correct?", justification='center')],
                                      [sg.Text("ID: "),
                                       sg.Input(user_id, key='input_id', disabled=True)],
                                      [sg.Text("Team: "), sg.Combo(
                                          ["", "Programming", "Mechanical", "Shop", "Marketing", "Electrical"],
                                          key='select_team', expand_y=True, default_value=team)],
                                      [sg.Text("First: "), sg.Input(first, key='input_first')],
                                      [sg.Text("Last: "), sg.Input(last, key='input_last')],
                                      [sg.Button("Cancel"), sg.Button("Save Changes")]])
    while True:
        event, values = window.read()
        if event == "Save Changes":
            user_id = values['input_id']
            team = values['select_team']
            first = values['input_first']
            last = values['input_last']

            # if duplicate id (card has already been used before) updates instead of adding new entry
            cursor.execute(
                "INSERT INTO members (member_id, first_name, last_name, team_section) VALUES (%s, %s, %s, %s) "
                "ON DUPLICATE KEY UPDATE first_name = VALUES(first_name), last_name = VALUES("
                "last_name), team_section = VALUES(team_section)",
                (user_id, first, last, team))
            mydb.commit()
            break
        if event == sg.WIN_CLOSED or event == "Cancel":
            break
    window.close()


def fetch_page(table, page, cursor):
    start_index = page * PAGE_SIZE
    cursor.execute(f"SELECT * FROM {table} LIMIT {start_index}, {PAGE_SIZE}")
    return [list(i) for i in cursor.fetchall()]


# window to view and edit the database
def db_window(mydb, cursor):
    page_num = 0
    selected_table = 'members'
    # Define the window layout
    layout = [
        [sg.Button('Show members table'), sg.Button('Show attendance table')],
        [sg.Table(values=[], headings=["Member ID", "First Name", "Last Name", "Team"], auto_size_columns=True, display_row_numbers=True, key='db_table', enable_events=True)],
        [sg.Button('Edit selected row')],
        [sg.Button('Previous Page'), sg.Button('Next Page')]
    ]
    window = sg.Window("Database", layout, finalize=True)
    rows = fetch_page('members', page_num, cursor)
    window['db_table'].update(values=rows)
    while True:
        event, values = window.read()
        # End program if user closes window or presses the 'Quit' button
        if event == sg.WINDOW_CLOSED:
            break

        elif event == 'Show members table':
            selected_table = 'members'
            rows = fetch_page('members', page_num, cursor)
            window['db_table'].update(values=rows)

        elif event == 'Show attendance table':
            selected_table = 'attendance'
            rows = fetch_page('attendance', page_num, cursor)
            window['db_table'].update(values=rows)

        elif event == 'Edit selected row':  # Triggered when a line in the Multiline element is clicked
            selected_row = values['db_table'][0]  # This assumes each row is on a separate line
            if selected_table == 'members':
                edit_member_entry(mydb, cursor, rows[selected_row])

            # Refresh table
            rows = fetch_page(selected_table, page_num, cursor)
            window['db_table'].update(values=rows)

        elif event == 'Previous Page':
            if page_num > 0:
                page_num -= 1
                rows = fetch_page(selected_table, page_num, cursor)
                window['db_table'].update(values=rows)

        elif event == 'Next Page':
            page_num += 1
            rows = fetch_page(selected_table, page_num, cursor)
            window['db_table'].update(values=rows)


# opens window to edit a row in the members table
def edit_member_entry(mydb, cursor, selected_row):
    user_id, first, last, team = selected_row  # Assumes first column is a unique identifier
    temp_id = user_id
    window = sg.Window("Edit member", [[sg.Text("ID: "), sg.Input(user_id, key='input_id')],
                                       [sg.Text("Team: "), sg.Combo(
                                           ["", "Programming", "Mechanical", "Shop", "Marketing", "Electrical"],
                                           key='select_team', expand_y=True, default_value=team)],
                                       [sg.Text("First: "), sg.Input(first, key='input_first')],
                                       [sg.Text("Last: "), sg.Input(last, key='input_last')],
                                       [sg.Button("Cancel"), sg.Button("Save Changes")]])
    while True:
        event, values = window.read()
        if event == "Save Changes":
            user_id = values['input_id']
            team = values['select_team']
            first = values['input_first']
            last = values['input_last']

            # if duplicate id (card has already been used before) updates instead of adding new entry
            cursor.execute("UPDATE members SET first_name = %s, last_name = %s, team_section = %s, member_id = %s WHERE member_id = %s", (first, last, team, user_id, temp_id))
            mydb.commit()
            break
        if event == sg.WIN_CLOSED or event == "Cancel":
            break
    window.close()


# opens window to edit a row in the attendance table
def edit_attendance_entry(mydb, cursor, selected_row):
    timestamp, member_id = selected_row.split(',')
    placeholder = timestamp
    window = sg.Window("Edit Attendance",
                       [[sg.Text("Timestamp: "), sg.Input(member_id, key='input_time')],
                        [sg.Text("ID: "), sg.Input(team, key='input_id')],
                        [sg.Button("Cancel"), sg.Button("Save Changes")]])
    while True:
        event, values = window.read()
        timestamp = values["input_time"]
        member_id = values['input_id']
        if event == "Save Changes":
            # if duplicate id (card has already been used before) updates instead of adding new entry
            cursor.execute("UPDATE attendance SET check_in_time = %s, check_in_id = %s WHERE check_in_time = %s", (timestamp, member_id, placeholder))
            mydb.commit()
            break
        if event == sg.WIN_CLOSED or event == "Cancel":
            break
    window.close()


def main():
    try:
        mydb = mysql.connector.connect(
            host="localhost",
            database='attendance',
            user="root",
            password=""
        )
        if mydb.is_connected():
            cursor = mydb.cursor()
    except Error as e:
        print("Error with MySQL", e)
        exit()

    window = sg.Window("Attendance", [[sg.Text("Tap a card/tag to the scanner to view/edit current info")],
                                      [sg.Button("Edit Database")]])

    # Create an event loop
    while True:
        event, values = window.read(timeout=250)  # moves on to check reader after 250ms
        # if on the check in screen, poll for successful scan
        if event == "Edit Database":
            db_window(mydb, cursor)
        user_id = readUID()
        if user_id is not None:
            # if True:  # placeholder for id scanner
            cursor.execute("SELECT first_name, last_name, team_section FROM members WHERE member_id = (%s)", (user_id,))
            row = cursor.fetchone()
            if row:
                confirm_window(user_id, mydb, cursor, row[0], row[1], row[2])
            else:
                confirm_window(user_id, mydb, cursor)
        if event == sg.WIN_CLOSED:
            break
    # clean up
    window.close()
    if mydb.is_connected():
        cursor.close()
        mydb.close()


if __name__ == '__main__':
    main()
