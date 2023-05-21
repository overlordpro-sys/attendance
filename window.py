# hello_psg.py

import PySimpleGUI as sg
import mysql.connector
from mysql.connector import Error
import time
import datetime
# from mfrc522 import SimpleMFRC522


def confirm_window(first, last, team, id):
    confirm_id = [sg.Text("ID: "), sg.Input(id, enable_events=False, disabled=True, key='ci_id')]
    confirm_info = [sg.Text('Team: '), sg.Input(team, enable_events=False, disabled=True, key='ci_team'),
                    sg.Text("Name: "),
                    sg.Input(first + last, enable_events=False, disabled=True, key='ci_name')]
    window = sg.Window("Attendance", [[sg.Text("Is this you?", justfification='center')], confirm_id, confirm_info,
                                      [sg.Button("Confirm")]])
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    while True:
        event, values = window.read()
        if event == "Confirm":
            print("temp")
        if event == sg.WIN_CLOSED:
            break
    window.close()


def main():
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

    ci_title = sg.Text("Tap your card/tag to the scanner to check in", key='ci_title')
    ci_db_button = sg.Button("See DB")

    ci_screen = [[ci_title, sg.Push(), ci_db_button]]

    db_screen = [[sg.Text("DB_placeholder"), sg.Button("Back")]]

    # Create the layout for switching screens
    layout = [[sg.Column(ci_screen, key='ci_screen'), sg.Column(db_screen, visible=False, key='db_screen')],
              ]
    # Create the window
    window = sg.Window("Attendance", layout)

    # Initialize the scanner
    # reader = SimpleMFRC522()

    # Create an event loop
    while True:
        event, values = window.read(timeout=250)  # times out after 250ms
        # code for cycling screens
        if event == "See DB":
            window['ci_screen'].update(visible=False)
            window['db_screen'].update(visible=True)
        if event == "Back":
            window['ci_screen'].update(visible=True)
            window['db_screen'].update(visible=False)
        # if on the check in screen, poll for successful scan
        if window['ci_screen'].visible:
            # id, text = reader.read_no_block()
            # if id is not None:
            if True:  # placeholder for id scanner
                # cursor.execute("SELECT first_name, last_name, team_section FROM members WHERE id = %s", id)
                # row = cursor.fetchone()
                row = True
                if row:
                    confirm_window("Brent", "Lee", "Programming", 1)
                    # confirm_window(row[0], row[1], row[2], id)
                else:
                    sg.popup_error("ID not found in database", title="Error")

        if event == sg.WIN_CLOSED:
            break
    window.close()
    if mydb.is_connected():
        cursor.close()
        mydb.close()


if __name__ == '__main__':
    main()
