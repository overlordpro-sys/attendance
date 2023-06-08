#!/usr/bin/env python
import mysql.connector

mydb = mysql.connector.connect(
  host="localhost",
  user="pi4470",
  password="pi4470"
)

mycursor = mydb.cursor()

mycursor.execute("CREATE DATABASE attendance;")
mycursor.execute("USE attendance;")
memberQuery = """CREATE TABLE members (
                member_id varchar(20) primary key,
                first_name varchar(20) not null,
                last_name varchar(20) not null,
                team_section varchar(20) not null
)"""
mycursor.execute(memberQuery)

attQuery = """CREATE TABLE attendance (
                check_in_time timestamp not null,
                check_in_id varchar(20) not null
)"""
mycursor.execute(attQuery)

for x in mycursor:
  print(x)

