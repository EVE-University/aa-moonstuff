# Moonstuff

Moonstuff is a plugin for [AllianceAuth](https://gitlab.com/allianceauth/allianceauth) to allow alliances to better manage moons and their
extraction schedules.

## Installation

Install the project from git to your allianceauth venv.

```bash
source /path/to/auth/venv/activate
pip install git+https://gitlab.com/colcrunch/aa-moonstuff
```

The add it to your `INSTALLED-APPS` in `local.py`.
```python
INSTALLED_APPS+=[
        'moonstuff',
    ]
```

Then run migrations and restart your supervisor processes.

After restarting your supervisor processes, run the `moonstuff.tasks.pull_ore_types` task to populate your database with a list of Ore types.

### Task Schedule
Add the following to the end of your `local.py`:
```python
CELERYBEAT_SCHEDULE['run_moonstuff_data_import'] = {
    'task': 'moonstuff.tasks.import_data',
    'schedule': crontab(minute='30'),
}
```

To keep ore values up to date, you will also want to schedule the `moonstuff.tasks.calc_ore_values` at a regular interval. Once per week or once per month should be often enough.

Alternatively, you can go to the django admin page and add the task at `[your auth url]/admin/django_celery_beat/periodictask/` 

## Permissions

The permissions for this plugin are rather straight forward.

* `moonstuff.view_moonstuff` - This is access permission, users without this permission will be unable to access the plugin.
* `moonstuff.add_resource` - This permission allows users to upload moon scan data.
* `moonstuff.add_extractionevent` - This permission is allows users to add their tokens to be pulled from when checking for new extraction events. 
 