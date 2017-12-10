# Django Project "CCTV Management System"
This is a demo of Django project **without ORM**, which means 'models' wasn't used for database connection and controling.
All SQL queries are directly excuted by MySQLdb.

Authors: [Wang Gengyu(me)](wanggeengyu.com), Michelle Pyh and Melissa Kee together.

## Main Features
* User Authentication
* Show, add, edit, delete and search database records
* Modify database recodes with reference constraints
* Upload and download files

## Environment Requirment
* Python 3.6, Django 1.11, MySQL
* Python Packages Dependency: MySQLdb, datetime, time, csv, os, urllib.parse

## How to run it
1. Set environment and install necessary python packages
2. Modify database setting with your own databse account in view.py
3. Import dump.sql to your database
4. Run server by 'python manage.py runserver' in code directory
