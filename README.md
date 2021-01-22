# Moonstuff

Moonstuff is a plugin for [AllianceAuth](https://gitlab.com/allianceauth/allianceauth) to allow alliances to better manage moons and their
extraction schedules.

# Rewrite Branch
***THIS IS A DEV BRANCH! CODE ON THIS BRANCH IS WIP, AND NOT READY FOR PROD.***

***Note on Migrations:*** I will likely be squashing migrations before merging rewrite into master.

### Setting
`MOON_REFINE_PERCENT` - Define the refine rate to be used when calculating moon value. (Default value: 87.6)

### Permissions

| Permission Name | Admin Site | Auth Site |
|-----------------|------------|-----------|
|Moonstuff.access_moonstuff | None | Can access the moonstuff module.|
|Resource.add_resource | None | Can add access the add_scan page to add moon scan data. |
|TrackingCharacter.add_trackingcharacter | None | Can link a character to be used in tracking extractions. |

### Scopes
Though accepted best practice for auth is to ensure that one's ESI application has access to all
scopes through the EVE Development portal, if you are not following this practice please make sure to 
include the following scopes in your ESI application.

| Scope | Purpose |
|-------|---------|
|esi-industry.read_corporation_mining.v1| This is required to pull corporation moon extraction data. (The in-game Station_Manager and Accountant roles are required) |
|esi-universe.read_structures.v1 | Required to pull structure names. |
|esi-characters.read_notifications.v1| Required to pull character notifications used for updating resource data. |