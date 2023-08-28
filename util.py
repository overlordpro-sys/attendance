import datetime
from calendar import monthrange
from datetime import datetime

import PySimpleGUI as sg
from smartcard.scard import *
from smartcard.util import toHexString


# opens window to edit the user data associated with a rfid tag in the database
def edit_window(user_id, mydb, cursor, first="", last="", team=""):
    window = sg.Window("Create/Edit", [[sg.Text("ID: "),
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


# opens a window to create a new member entry
def create_member_entry(mydb, cursor):
    # manually creating one with an id is unrealistic, but the option is provided anyway
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
    timestamp = selected_row[0]
    member_id = selected_row[1]
    temp_timestamp = timestamp
    # sets up elements with their current values set to those from the database
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
            # formats the user's input into timestamp format
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


# opens a window to create a new attendance entry
def create_attendance_entry(mydb, cursor):
    timestamp = datetime.now()
    # defaults input boxes to current time and sets day options to suitable days in specified month
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
        # Error thrown if day is invalid for selected month and year
        except ValueError as e:
            sg.popup_error(e, title="Error", grab_anywhere=True)
    window.close()


def readUID():
    result, context = SCardEstablishContext(SCARD_SCOPE_USER)
    if result != SCARD_S_SUCCESS:
        sg.popup_error("Failed to transmit", SCardGetErrorMessage(result))
        exit()
    result, readers = SCardListReaders(context, [])
    if len(readers) < 1:
        sg.popup_error("Reader not detected", "Is the reader plugged in?")
        exit()
    reader = readers[0]
    result, card, protocol = SCardConnect(
        context,
        reader,
        SCARD_SHARE_SHARED,
        SCARD_PROTOCOL_T0 | SCARD_PROTOCOL_T1)
    try:
        result, response = SCardTransmit(card, protocol, [0xFF, 0xCA, 0x00, 0x00, 0x04])
        uid = toHexString(response, format=0).replace(" ", "")
        return int(uid, 16)
    except SystemError:
        return None


def login():
    user = '4470'
    passw = '4470'
    layout = [[sg.Text("Username:"), sg.Input(key='username')],
              [sg.Text("Password:"), sg.Input(key='password')],
              [sg.Button("Login"), sg.Push(), sg.Button("Cancel")]]
    window = sg.Window("Login", layout)
    while True:
        event, values = window.read()
        if event == "Login":
            if values['username'] == user and values['password'] == passw:
                window.close()
                return True
            else:
                sg.popup_error("Incorrect username/password")
        if event == sg.WIN_CLOSED or event == "Cancel":
            window.close()
            return False


if __name__ == '__main__':
    while True:
        print(readUID())
