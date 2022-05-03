<img src="https://i.imgur.com/zPP83aX.png" title="VUSualiser" alt="VUSualiser">

# VUSualiser

> A web interface that allows searching through Variant of Unknown Significance (VUS).

Important dependencies: 
- [Python 3.6.8 or higher](https://www.python.org/)
  - [Flask](https://pypi.org/project/Flask/)
  - [Flask-PyMongo](https://pypi.org/project/Flask-PyMongo/)
  - [Flask-Login]()
- [MongoDB](https://www.mongodb.com/)
- [datatables.js](https://datatables.net/)
- [alissa_interpret_client] (https://github.com/UMCUGenetics/alissa_interpret_client)


## Application Structure 
```
.
|──────run.py - used to run the flask app, also doubles as .wsgi file
|──────run_local.py - used to run the flask app on your local machine
|──────src/
| |────__init__.py - creats the needed managers for Flask, Flask-PyMongo and Flask-Login
| |────config.py - configuration for the whole app
| |────datatable.py - class for querying MongoDB on the backend, returns data for datatables.js
| |────forms.py - contains Flask-WTF forms
| |────models.py - contains user model
| |────static/ (.css .js .png)
| |────templates/ (.html)
| |────views/ (.py)
| | |──main.py - manages handling for urls
| | |──auth.py - manages handling for account-related urls, eg. /login, /logout, etc.
|──────extra/
| |────import_data.py - loads new analyses from Alissa to import in MongoDB (VUSualizer)
| |────config.py - configuration for the import data script
| |────logging_config.yml - for logging files of the import data script
```

### [Datatables.js Server-side Processing](https://datatables.net/manual/server-side)
Due to the amount of data, data needs to be filtered through the server.

As of right now, two templates contain the client-sided datatables.js code:
- base.html
- all.html

There are some "apis" that datatables.js interacts with. They are accessed through:
- /_get_all_data
- /_get_variant_data
- /_get_gene_data
- /_get_patient_data

These urls are handled in main.py. The program then uses the DataTablesServer class from datatable.py to query the database and return the data back to datatables.js to create a table that can be clicked through. 


## Installation

1. Make a Python 3.6.8 venv in correct spot on server and install any requirements with pip:
```
$ python3 -m venv venv
$ source ./venv/bin/activate
$ pip install -r requirements.txt
```
2. Install MongoDB
3. Load data into MongoDB with script in the "extra" folder.
4. (Optional) Configurate MONGO_URI in config.py if you're using different user details and/or database name
5. Configure the config.py (in extra folder) for Alissa credentials and logging_config.yml location
6. Add crontab to automatically check Alissa for new analyses (example shown below. every day on 3AM). This needs to be done with the admin user of the server. 
```
$ 0 3 * * * /path/to/VUSualizer/extra/import_data.py >> /path/to/VUSualizer/extra/cronlogs.log 2>&1
```

## Run for development
Activate venv
```
$ python run.py
```
## Run for production (apache required)
```
$ mod_wsgi-express start-server run.py
```

## Run on local machine
1. Configure the config.py (in extra folder) for Alissa credentials
2. If development for import_data.py (not required for running app) --> 
  - Change shebang python to ```#!/usr/bin/env python3``` or local equivalent
  - Change filename parameter in logging_config.yml to correct local path
3. Activate venv
4. Run run_local.py
```
$ python run_local.py
```

## Troubleshooting
### Webpage does not load:
1. Not connected to the UMCU server (either via VPN, on location (WiFi) or follow-me workspace)
2. Service needs to be restarted:
```
$ sudo /bin/systemctl stop vusualizer-wsgi.service
$ sudo /bin/systemctl start vusualizer-wsgi.service
```
