from datetime import datetime

import PySimpleGUI as sg
import mysql.connector
from mysql.connector import Error
from admin_only import admin_window
from util import readUID, edit_window, login


def confirm_window(user_id, first, last, team, mydb, cursor):
    window = sg.Window("Attendance", [[sg.Text("Is this you?", justification='center')],
                                      [sg.Text("ID: "), sg.Input(user_id, enable_events=False, disabled=True)],
                                      [sg.Text('Team: '), sg.Input(team, enable_events=False, disabled=True)],
                                      [sg.Text("Name: "),
                                       sg.Input(first + " " + last, enable_events=False, disabled=True)],
                                      [sg.Button("Confirm", bind_return_key=True)]])
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    while True:
        event, values = window.read()
        if event == "Confirm":
            cursor.execute("INSERT INTO attendance (check_in_time, check_in_id) VALUES (%s, %s)", (now, user_id))
            mydb.commit()
            print(cursor.rowcount)
            break
        if event == sg.WIN_CLOSED:
            break
    window.close()


def main():
    cursor = None
    try:
        mydb = mysql.connector.connect(
            host="localhost",
            database='attendance',
            user="pi4470",
            password="pi4470"
        )
        if mydb.is_connected():
            cursor = mydb.cursor()
    except Error as e:
        print("Error with MySQL", e)
        exit()

    # Create the layout for switching screens
    layout = [[sg.VPush(), sg.Push(), sg.Button("Login to Admin")],
              [sg.Text("Tap your card/tag to the scanner to check in", font=('Arial', 20))],
              [sg.VPush()]]
    # Create the window
    window = sg.Window("Attendance", layout, resizable=True, element_justification='c')

    # Create an event loop
    while True:
        event, values = window.read(timeout=100)  # times out after 250ms
        # code for cycling screens
        # if on the check in screen, poll for successful scan
        user_id = readUID()
        if user_id is not None:
            # if True:  # placeholder for id scanner
            cursor.execute("SELECT first_name, last_name, team_section FROM members WHERE member_id = (%s)", (user_id,))
            row = cursor.fetchone()
            if row:
                confirm_window(user_id, row[0], row[1], row[2], mydb, cursor)
            else:
                ch = sg.popup_yes_no("ID not found in database", "Create new user?", font=('Arial', 15))
                if ch == "Yes":
                    edit_window(user_id, mydb, cursor)
        if event == sg.WIN_CLOSED:
            break
        if event == 'Login to Admin':
            if login():
                admin_window(mydb, cursor)
    # cleanup
    window.close()
    if mydb.is_connected():
        cursor.close()
        mydb.close()


if __name__ == '__main__':
    main()
