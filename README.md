<img src="https://i.imgur.com/zPP83aX.png" title="VUSualiser" alt="VUSualiser">

# VUSualiser

> A web interface that allows searching through Variant of Unknown Significance (VUS).

Important dependencies: 
- [Python 3.7](https://www.python.org/)
  - [Flask](https://pypi.org/project/Flask/)
  - [Flask-PyMongo](https://pypi.org/project/Flask-PyMongo/)
  - [Flask-Login]()
- [MongoDB](https://www.mongodb.com/)
- [datatables.js](https://datatables.net/)


## Application Structure 
```
.
|──────run.py - used to run the flask app, also doubles as .wsgi file)
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

1. Make a Python 3.7 venv and install any requirements with pip:
```
$ pip install -r requirements.txt
```
2. Install MongoDB
3. Load data into MongoDB with script in the "extra" folder.
4. (Optional) Configurate MONGO_URI in config.py if you're using different user details and/or database name

## Run for development
```
$ python run.py
```
## Run for production (apache required)
```
$ mod_wsgi-express start-server run.py
```
