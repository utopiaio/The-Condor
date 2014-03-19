#The Condor

The name is from he Movie [Reno 911 (The Rock)](https://www.youtube.com/watch?v=H53kBYo1Jx8)

##Features
- Built with Python, what more do i need to say
- Automatic Report Card (PDF)
- Grading support on non-numeric subjects (A, B, C...)
- Calender year division in to semesters
- Ranking [supports SAME ranking i.e. 1, 1, 3]
- Permission
- Student Transfer / Migration at end of Academic year
- Mark Input validation
- e-mail and SMS notification [via twilio]
- front web page [public website]

##Installation
- Well you need Windows --- naa, am kidding can you imagine, you'll need a Mac or Linux running Python 2.7.4+
- install pip
```bash
    $sudo apt-get install python-pip
```
- install virtual environment for python if you don't like to live DANGOURSLY
```bash
    $sudo pip install virtualenv
```
- now here comes to tricky part, you have to download the repository [by which you'll need an Internet connection, good luck]
- if you are reading this that means you *somehow* found an Internet connection and have downloaded the repository
- extract the file
- change to the directory of the extracted file
- create your PLAY ground
```bash
    $virtualenv [enviroment_name]
```
- activate it [you should see a red light when you do --- like a terminator]
```bash
    $source [enviroment_name]/bin/activate
```
- now install the requirements
```bash
    $pip install -r requirements.txt
```
- run a few commands
```
    $python manage.py syncdb
    $python manage.py runserver
```
- and voilà

##Heads Up
- i did NOT stress on static files for the *front* page, i just created a *fake* app so to store the files and serve them from there BUT you and i know it's wrong
- you might run in to problems installing `Pillow` and `reportlab`, so be sure to read their documentation for PROPER pip install
- the app is designed for St. Joseph school it's PONTLESS making the app *generic* since EVERY school follows a DIFFRENT style on reporting, grading...
- the app can be EASILY tweaked so suit EVERY need
- go to `setting.py` and set a few values, most values are set for development, if you want to deploy it make sure to change the values to the appropriate one [mostly from console to REAL world]
```python
    EMAIL_USE_TLS = True
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_HOST_USER = ''
    EMAIL_HOST_PASSWORD = ''
    EMAIL_PORT = 587
    EMAIL_FROM = 'info@demo.com'
    EMAIL_SUBJECT = 'St. Joseph School'
```

###Finally
- send me a pull request if you have any
- ENJOY!
