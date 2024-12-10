# lte_long_duration

This script queries NCM for Cradlepoint routers that are stuck in LTE failover.

## Dependencies

* ncm: https://pypi.org/project/ncm/
* prettytable: https://pypi.org/project/prettytable/
* NCM API Keys, in file `apikeys.ini` in the working directory

## apikeys.ini sample

```
[KEYS]
X-CP-API-ID = ...
X-CP-API-KEY = ...
X-ECM-API-ID = ...
X-ECM-API-KEY = ...
```