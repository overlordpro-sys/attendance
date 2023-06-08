import datetime
from calendar import monthrange
from datetime import datetime
import PySimpleGUI as sg
import mysql.connector
from mysql.connector import Error

from read import readUID

PAGE_SIZE = 10  # Change this to whatever page size you want


# window to edit the user data associated with a rfid tag in the database
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


def update_table(window, table, page, cursor, where=""):
    start_index = page * PAGE_SIZE
    print(f"SELECT * FROM {table} {where} LIMIT {start_index}, {PAGE_SIZE}")
    cursor.execute(f"SELECT * FROM {table} {where} LIMIT {start_index}, {PAGE_SIZE}")
    rows = [list(i) for i in cursor.fetchall()]
    if table == 'members':
        window['members_table'].update(values=rows)
    else:
        window['attendance_table'].update(values=rows)
    return rows


# window to view and edit the database
def db_window(mydb, cursor):
    member_page_num = 0
    attendance_page_num = 0
    selected_table = 'members'
    # Define the window layout
    layout = [
        [sg.Button('Show members table'), sg.Button('Show attendance table')],
        [sg.Text("Search by"),
         sg.Column([[sg.Combo(["ID", "Team", "First", "Last"], default_value="ID", enable_events=True, readonly=True,
                              key='members_search_combo'), sg.Input(key='members_search_input', enable_events=True)]],
                   key='members_search_col'),
         sg.Column([[sg.Combo(["Date", "ID"], default_value="Date", enable_events=True, readonly=True,
                              key='attendance_search_combo'),
                     sg.Input(key='attendance_search_input', enable_events=True, visible=False),
                     sg.Text("Year", key='year_text'),
                     sg.Input(key='attendance_search_year', size=(5, 1), enable_events=True),
                     sg.Text("Month", key='month_text'),
                     sg.Input(key='attendance_search_month', size=(5, 1), enable_events=True),
                     sg.Text("Day", key='day_text'),
                     sg.Input(key='attendance_search_day', size=(5, 1), enable_events=True)]],
                   key='attendance_search_col',
                   visible=False)],
        [sg.Table(values=[[]], headings=[" Member ID ", "First Name", "Last Name", "   Team   "],
                  display_row_numbers=True, key='members_table', enable_events=True, expand_x=True, expand_y=True,
                  hide_vertical_scroll=True, justification='center'),
         sg.Table(values=[], headings=["   Timestamp   ", " Member ID "], display_row_numbers=True,
                  key='attendance_table',
                  enable_events=True, visible=False, expand_x=True, expand_y=True, hide_vertical_scroll=True,
                  justification='center')],
        [sg.Button('Edit selected row'), sg.Button('Delete selected row'), sg.Button('Create entry')],
        [sg.Button('Previous Page'), sg.Button('Next Page')]
    ]
    window = sg.Window("Database", layout, finalize=True, size=(700, 350), resizable=True)
    rows = update_table(window, 'members', member_page_num, cursor)
    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED:
            break
        elif event == 'members_search_combo' or event == 'members_search_input':
            search = values['members_search_input']
            if search != "":
                match values['members_search_combo']:
                    case "ID":
                        rows = update_table(window, 'members', member_page_num, cursor,
                                            f" WHERE member_id LIKE '%{search}%'")
                    case "Team":
                        rows = update_table(window, 'members', member_page_num, cursor,
                                            f" WHERE team_section LIKE '%{search}%'")
                    case "First":
                        rows = update_table(window, 'members', member_page_num, cursor,
                                            f" WHERE first_name LIKE '%{search}%'")
                    case "Last":
                        rows = update_table(window, 'members', member_page_num, cursor,
                                            f" WHERE last_name LIKE '%{search}%'")
            else:
                rows = update_table(window, 'members', member_page_num, cursor)
        elif event == 'attendance_search_combo' or event == 'attendance_search_input' or \
                event == 'attendance_search_year' or event == 'attendance_search_month' or event == 'attendance_search_day':
            if values['attendance_search_combo'] == 'Date':
                window['attendance_search_input'].update(visible=False)
                window['year_text'].update(visible=True)
                window['attendance_search_year'].update(visible=True)
                window['month_text'].update(visible=True)
                window['attendance_search_month'].update(visible=True)
                window['day_text'].update(visible=True)
                window['attendance_search_day'].update(visible=True)
            else:
                window['attendance_search_input'].update(visible=True)
                window['year_text'].update(visible=False)
                window['attendance_search_year'].update(visible=False)
                window['month_text'].update(visible=False)
                window['attendance_search_month'].update(visible=False)
                window['day_text'].update(visible=False)
                window['attendance_search_day'].update(visible=False)
            search = values['attendance_search_input']
            year = values['attendance_search_year']
            month = values['attendance_search_month']
            day = values['attendance_search_day']
            if search != "" or (year != "" and month != "" and day != ""):
                match values['attendance_search_combo']:
                    case "Date":
                        try:
                            dt = datetime(int(year), int(month), int(day)).date()
                            rows = update_table(window, 'attendance', attendance_page_num, cursor,
                                                f" WHERE date(check_in_time) = '{dt}'")
                        except ValueError:
                            pass
                    case "ID":
                        rows = update_table(window, 'attendance', attendance_page_num, cursor,
                                            f" WHERE check_in_id LIKE '%{search}%'")
            else:
                rows = update_table(window, 'attendance', attendance_page_num, cursor)
        elif event == 'attendance_search_combo':
            pass
        elif event == 'Show members table':
            selected_table = 'members'
            rows = update_table(window, 'members', member_page_num, cursor)
            window['members_table'].update(visible=True)
            window['members_search_col'].update(visible=True)
            window['attendance_table'].update(visible=False)
            window['attendance_search_col'].update(visible=False)
        elif event == 'Show attendance table':
            selected_table = 'attendance'
            rows = update_table(window, 'attendance', attendance_page_num, cursor)
            window['attendance_table'].update(visible=True)
            window['attendance_search_col'].update(visible=True)
            window['members_table'].update(visible=False)
            window['members_search_col'].update(visible=False)
        elif event == 'Edit selected row':
            table = 'members_table' if selected_table == 'members' else 'attendance_table'
            if len(values[table]) < 1:
                sg.popup_error("Row not selected", title="Error", grab_anywhere=True)
            else:
                selected_row = values[table][0]
                if selected_table == 'members':
                    edit_member_entry(mydb, cursor, rows[selected_row])
                else:
                    edit_attendance_entry(mydb, cursor, rows[selected_row])
            rows = update_table(window, selected_table,
                                member_page_num if selected_table == 'members' else attendance_page_num, cursor)
        elif event == 'Delete selected row':
            table = 'members_table' if selected_table == 'members' else 'attendance_table'
            if len(values[table]) < 1:
                sg.popup_error("Row not selected", title="Error", grab_anywhere=True)
            else:
                selected_row = rows[values[table][0]]
                query = f"DELETE FROM {selected_table} WHERE "
                if selected_table == 'members':
                    query += f"member_id = %s AND first_name = %s"
                else:
                    query += f"check_in_time = %s AND check_in_id = %s"
                popup = sg.popup_ok_cancel("Press Ok to delete or cancel", title="Confirm")
                if popup == "OK":
                    cursor.execute(query, (selected_row[0], selected_row[1]))
                    mydb.commit()
                rows = update_table(window, selected_table,
                                    member_page_num if selected_table == 'members' else attendance_page_num, cursor)
        elif event == 'Create entry':
            if selected_table == "members":
                create_member_entry(mydb, cursor)
            else:
                create_attendance_entry(mydb, cursor)
            rows = update_table(window, selected_table,
                                member_page_num if selected_table == 'members' else attendance_page_num, cursor)
        elif event == 'Previous Page':
            if selected_table == "members" and member_page_num > 0:
                member_page_num -= 1
                rows = update_table(window, 'members', member_page_num, cursor)
            if selected_table == "attendance" and attendance_page_num > 0:
                attendance_page_num -= 1
                rows = update_table(window, 'attendance', attendance_page_num, cursor)
        elif event == 'Next Page':
            if selected_table == "members":
                member_page_num += 1
                rows = update_table(window, 'members', member_page_num, cursor)
            else:
                attendance_page_num += 1
                rows = update_table(window, 'attendance', attendance_page_num, cursor)


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
            cursor.execute(
                "UPDATE members SET first_name = %s, last_name = %s, team_section = %s, member_id = %s WHERE member_id = %s",
                (first, last, team, user_id, temp_id))
            mydb.commit()
            break
        if event == sg.WIN_CLOSED or event == "Cancel":
            break
    window.close()


def create_member_entry(mydb, cursor):
    window = sg.Window("Edit member", [[sg.Text("ID: "), sg.Input(key='input_id')],
                                       [sg.Text("Team: "), sg.Combo(
                                           ["", "Programming", "Mechanical", "Shop", "Marketing", "Electrical"],
                                           key='select_team', expand_y=True, default_value="")],
                                       [sg.Text("First: "), sg.Input(key='input_first')],
                                       [sg.Text("Last: "), sg.Input(key='input_last')],
                                       [sg.Button("Cancel"), sg.Button("Create entry")]])
    while True:
        event, values = window.read()
        if event == "Create entry":
            member_id = values['input_id']
            first = values['input_first']
            last = values['input_last']
            team = values['select_team']
            cursor.execute("INSERT INTO members (member_id, first_name, last_name, team_section) "
                           "VALUES (%s, %s, %s, %s)", (member_id, first, last, team))
            mydb.commit()
            break
        if event == sg.WIN_CLOSED or event == "Cancel":
            break
    window.close()


# opens window to edit a row in the attendance table
def edit_attendance_entry(mydb, cursor, selected_row):
    timestamp, member_id = selected_row
    temp_timestamp = timestamp
    window = sg.Window("Edit Attendance",
                       [[sg.Text("Year"), sg.Input(timestamp.year, key='year', enable_events=True), sg.Text("Month"),
                         sg.Combo(default_value=timestamp.month, values=[i for i in range(1, 13)], key='month',
                                  enable_events=True),
                         sg.Text("Day"),
                         sg.Combo([i for i in range(1, monthrange(timestamp.year, timestamp.month)[1] + 1)],
                                  default_value=timestamp.day, key='day', enable_events=True)],
                        [sg.Text("Hour: "),
                         sg.InputCombo(default_value=timestamp.hour, values=[i for i in range(1, 24)], key='hour',
                                       enable_events=True),
                         sg.Text("Minute: "),
                         sg.InputCombo(default_value=timestamp.minute, values=[i for i in range(1, 60)], key='minute',
                                       enable_events=True),
                         sg.Text("Second: "),
                         sg.InputCombo(default_value=timestamp.second, values=[i for i in range(1, 60)], key='second',
                                       enable_events=True)],
                        [sg.Text("ID: "), sg.Input(member_id, key='input_id')],
                        [sg.Button("Cancel"), sg.Button("Save Changes")]])
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == "Cancel":
            break
        try:
            timestamp = datetime(int(values['year']), int(values['month']), int(values['day']),
                                 int(values['hour']), int(values['minute']), int(values['second']))
            member_id = values['input_id']
            if event == "Save Changes":
                # if duplicate id (card has already been used before) updates instead of adding new entry
                cursor.execute("UPDATE attendance SET check_in_time = %s, check_in_id = %s WHERE check_in_time = %s",
                               (timestamp, member_id, temp_timestamp))
                mydb.commit()
                break
        except ValueError as e:
            sg.popup_error(e, title="Error", grab_anywhere=True)
    window.close()


def create_attendance_entry(mydb, cursor):
    timestamp = datetime.now()
    window = sg.Window("Edit Attendance",
                       [[sg.Text("Year"), sg.Input(timestamp.year, key='year', enable_events=True), sg.Text("Month"),
                         sg.Combo(default_value=timestamp.month, values=[i for i in range(1, 13)], key='month',
                                  enable_events=True),
                         sg.Text("Day"),
                         sg.Combo([i for i in range(1, monthrange(timestamp.year, timestamp.month)[1] + 1)],
                                  default_value=timestamp.day, key='day', enable_events=True)],
                        [sg.Text("Hour: "),
                         sg.InputCombo(default_value=timestamp.hour, values=[i for i in range(1, 24)], key='hour',
                                       enable_events=True),
                         sg.Text("Minute: "),
                         sg.InputCombo(default_value=timestamp.minute, values=[i for i in range(1, 60)], key='minute',
                                       enable_events=True),
                         sg.Text("Second: "),
                         sg.InputCombo(default_value=timestamp.second, values=[i for i in range(1, 60)], key='second',
                                       enable_events=True)],
                        [sg.Text("ID: "), sg.Input(key='input_id')],
                        [sg.Button("Cancel"), sg.Button("Save Changes")]])
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == "Cancel":
            break
        try:
            timestamp = datetime(int(values['year']), int(values['month']), int(values['day']),
                                 int(values['hour']), int(values['minute']), int(values['second']))
            member_id = values['input_id']
            if event == "Save Changes":
                # if duplicate id (card has already been used before) updates instead of adding new entry
                cursor.execute("INSERT INTO attendance (check_in_time, check_in_id) VALUES (%s, %s)",
                               (timestamp, member_id))
                mydb.commit()
                break
        except ValueError as e:
            sg.popup_error(e, title="Error", grab_anywhere=True)
    window.close()


def main():
    try:
        mydb = mysql.connector.connect(
            host="DESKTOP-PMU7J6N.local",
            database='attendance',
            user="pi4470",
            password="pi4470"
        )
        if mydb.is_connected():
            cursor = mydb.cursor()
    except Error as e:
        print("Error with MySQL", e)
        exit()

    window = sg.Window("Attendance", [[sg.VPush()],
                                      [sg.Text("Tap a card/tag to the scanner to view/edit current info",
                                               font=('Arial', 20))],
                                      [sg.Button("Edit Database", font=('Arial', 15), size=(20, 2))],
                                      [sg.VPush()]], resizable=True, element_justification='c')

    # Create an event loop
    while True:
        event, values = window.read(timeout=100)  # moves on to check reader after 250ms
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
