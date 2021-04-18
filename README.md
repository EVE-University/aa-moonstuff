# Moonstuff
![pypi latest version](https://img.shields.io/pypi/v/aa-moonstuff?label=latest)
![python versions](https://img.shields.io/pypi/pyversions/aa-moonstuff)
![django versions](https://img.shields.io/pypi/djversions/aa-moonstuff?label=django)
![license](https://img.shields.io/pypi/l/aa-moonstuff?color=green)


Moonstuff is a plugin for [AllianceAuth](https://gitlab.com/allianceauth/allianceauth) to allow alliances to better manage moons and their
extraction schedules.

## Rewrite Branch
***THIS IS A DEV BRANCH! CODE ON THIS BRANCH IS WIP, AND NOT READY FOR PROD.***

***Note on Migrations:*** I will likely be squashing migrations before merging rewrite into master.

## Contents
- [Overview](#overview)
- [Key Features](#key-features)
- [Screenshots](#screenshots)
- [Installation](#installation)
- [Updating](#updating)
- [Settings](#settings)
- [Permissions](#permissions)

## Overview
Moonstuff is an [AllianceAuth](https://gitlab.com/allianceauth/allianceauth) plugin focused on managing moons, from keeping track of moonscan
data to making sure everyone knows when and where the next extraction will be. 

## Key Features
* Automatically pulls upcoming extractions from ESI.
* Automatically updates ore composition, just in case CCP decides to shuffle moon ore around.
* Pulls mining ledger data for all extractions as they happen.
  * Mining Ledger Data is used to track whether or not extractions are jackpots.
  * [Coming Soon] A mining ledger explorer is planned.
* Per-m3 values are displayed per ore, customized based on a customizable refine percent. 
(So if you don't have a T2-rigged Null Sec Tatara and perfect skills, you can see a more realistic value)
* Search for R-value or ore type from moon list.


## Screenshots

### Dashboard
#### Calendar View
![h](Cal View)

#### Card View
![h](Card View)

##### Jackpot
![h](Jackpot Card)

### Moon Info
![h](Modal)
(Moon info page is identical)

### Moon List
![h](Moon List)

#### Search
![h](RSearch)

## Installation
### 1. Install App
Install the app into your allianceauth virtualenvironment via PIP.

```bash
$ pip install aa-moonstuff
```

### 2. Configure AA Settings
Configure your AA settings (`local.py`) as follows:
- Add `'moonstuff',` to `INSTALLED_APPS`
- Add the following lines to the end of your settings file to ensure that the proper tasks are scheduled to run

```python
# Moonstuff Module
CELERYBEAT_SCHEDULE['moonstuff_import_extraction_data'] = {
    'task': 'moonstuff.tasks.import_extraction_data',
    'schedule': crontab(minute='*/10'),
}
CELERYBEAT_SCHEDULE['moonstuff_run_ledger_update'] = {
    'task': 'moonstuff.tasks.update_ledger',
    'schedule': crontab(minute=0, hour='*'),
}
CELERYBEAT_SCHEDULE['moonstuff_run_refinery_update'] = {
    'task': 'moonstuff.tasks.update_refineries',
    'schedule': crontab(minute=0, hour=0),
}
CELERYBEAT_SCHEDULE['moonstuff_run_price_update'] = {
    'task': 'moonstuff.tasks.load_prices',
    'schedule': crontab(minute=0, hour=0),
}
``` 

### 3. Run Migrations
Run migrations and copy static files.

```bash
$ python manage.py migrate
$ python manage.py collectstatic
```

Restart your supervisor tasks.

### 4. Load Eveuniverse Data
Run the following command to pull the required eveuniverse data required for moonstuff.

```bash
$ python manage.py moonstuff_preload_data
```

## Updating
To update your existing installation of Moonstuff first enable your virtual environment.

Then run the following commands from your allianceauth project directory (the one that contains `manage.py`).

```bash
$ pip install -U aa-moonstuff
$ python manage.py migrate
$ python manage.py collectstatic
```

Lastly, restart your supervisor tasks.

*Note: Be sure to follow any version specific update instructions as well. These instructions can be found on the `Tags` page for this repository.*


## Settings
`MOON_REFINE_PERCENT` - Define the refine rate to be used when calculating moon value. (Default value: 87.6)

## Permissions

| Permission Name | Admin Site | Auth Site |
|-----------------|------------|-----------|
|Moonstuff.access_moonstuff | None | Can access the moonstuff module.|
|Moonstuff.access_moon_list | None | Can access the list of known moons.|
|Resource.add_resource | None | Can add access the add_scan page to add moon scan data. |
|TrackingCharacter.add_trackingcharacter | None | Can link a character to be used in tracking extractions. |

## Scopes
Though accepted best practice for auth is to ensure that one's ESI application has access to all
scopes through the EVE Development portal, if you are not following this practice please make sure to 
include the following scopes in your ESI application.

| Scope | Purpose |
|-------|---------|
|esi-industry.read_corporation_mining.v1| This is required to pull corporation moon extraction data. (The in-game Station_Manager and Accountant roles are required) |
|esi-universe.read_structures.v1 | Required to pull structure names. |
|esi-characters.read_notifications.v1| Required to pull character notifications used for updating resource data. |

## Credits
This plugin makes use of [django-eveuniverse](https://gitlab.com/ErikKalkoken/django-eveuniverse) by @ErikKalkoken