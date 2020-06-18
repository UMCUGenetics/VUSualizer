<img src="https://i.imgur.com/zPP83aX.png" title="VUSualiser" alt="VUSualiser">

# VUSualiser

> Web interface, made with Python 3.7, Flask and MongoDB, that allows to search through Variant of Unknown Significance (VUS).

## Application Structure 
```
.
|──────run.py/
|──────src/
| |────__init__.py
| |────config.py
| |────datatable.py
| |────forms.py
| |────models.py
| |────static (.css .js .png)
| |────templates (.html)
| |────views (.py)

```

## Installation

1. Make a Python 3.7 venv and install any requirements with pip:
```
$ pip install -r requirements.txt
```
2. Setup MongoDB and use the correct MONGO_URI in config.py.
3. Load data into MongoDB with script in the "extra" folder.

## Run for development
```
$ python run.py
```
