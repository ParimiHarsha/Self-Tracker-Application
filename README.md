# Self-Tracker-Application
This is the implementation of a Self Tracker Application, which can be used to track event at a regular cadence**************************

## DB Schema Design

The database consists of 4 tables:

1)	User: 
user_id		INTEGER, primary key
	user_name	TEXT NOT NULL UNIQUE,
	password	TEXT NOT NULL,
2)	Tracker:
tracker_id	INTEGER, primary key
tracker_name	TEXT NOT NULL UNIQUE,
tracker_type	TEXT NOT NULL,
tracker_settings	TEXT
 	
3)	Assignment:
assignment_id 	INTEGER, primary key
tracker_id 	INTEGER NOT NULL, references tracker(tracker_id)
user_id	              INTEGER NOT NULL, references user(user_id)
log_id	              INTEGER NOT NULL, references logs(log_Id)

4)	Logs:
log_id   		INTEGER, primary
datetime	datetime NOT NULL,
value		TEXT NOT NULL,
notes		TEXT,

************************


The project is organized into various folders as shown in one of the screencasts. It contains:
•Application folder which contains:
 - Main.py
 - Config.py
 - Controllers.py
 - Database.py
 - Models.py
•Static folder which contains all the static files like the trendline and graphs
•Templates folder which contains all the html files required for the application

**************************

Once you open the folder you will find the project files in it. To run the application we need to run the main.py file and then run it in the broswer to start the application.
Then we can use the GUI to navigate around the application and to add trackers, add logs, perform all sorts of CRUD operations on it. To verify whether the app is running well we can
see the data being stored in the sqlite database which can be run using the DB Browser for SQlite.

Upload the unzipped files in a Directory and execute the main.py file.
