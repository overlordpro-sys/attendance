import PySimpleGUI as sg
import mysql.connector
from datetime import datetime
from mysql.connector import Error

from read import readUID


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

    # Create the layout for switching screens
    layout = [[sg.VPush()],
              [sg.Text("Tap your card/tag to the scanner to check in")],
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
                sg.popup_error("ID not found in database", title="Error", grab_anywhere=True)
        if event == sg.WIN_CLOSED:
            break
    # cleanup
    window.close()
    if mydb.is_connected():
        cursor.close()
        mydb.close()


if __name__ == '__main__':
    main()
