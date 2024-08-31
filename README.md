# Three-tier Solver


## Configuration
```
pip install -r requirements.txt
```

Make sure to have a directory link to CDGeB1\ in CDG-server\:
- open ```CMD.exe``` as Administrator
- cd into ```CDG-Server\```
- Type: ```mklink  /D CDGeB1 ..\CDGeB1```

## Running

### Run Web server locally:
```
cd src
python CDG-Server\application.py
```


### Run algorithm locally:
```
cd src
python -m CDGeB1.main
```

### Deploy to AWS
NOTE:
To this date (Aug 2024), AWS Elastic Beanstalk does not support Python 3.12, so avoid using syntax that is not supported by Python 3.12.

Preparation:
1. Don't forget to update the version number in relevant files
   - ```upload.html```
   - future files ...
2. Delete folders inside webappstorage\sessions
3. Delete output files inside datasets directory, if any

Steps:
1. ```cd CDG-Server```
2. ZIP the following into ```CDG-V0.X.zip```:
   - ```.ebextensions\```
   - ```CDGeB1\``` (use 7-Zip to include this link)
   - ```templates\```
   - ```webappstorage\```
   - ```__init__.py```
   - ```application.py```
   - ```requirements.txt```
4. AWS Beanstalk -> N. Virginia (us-east-1) -> Cdg-4-env -> Upload and deploy


## Misc

Debugging the Flask server in PyCharm:
https://stackoverflow.com/a/77159416

