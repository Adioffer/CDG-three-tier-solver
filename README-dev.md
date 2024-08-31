## Misc (Developers section)

### Run the algorithm locally:
```
cd cdg_server
python -m cdg_core.main
```

### Bugs

Debugging the Flask server in PyCharm:
https://stackoverflow.com/a/77159416



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
1. ```cd cdg_server```
2. ZIP the following into ```CDG-VX.Y.zip```:
   - ```.ebextensions\```
   - ```cdg_core\```
   - ```templates\```
   - ```webappstorage\```
   - ```__init__.py```
   - ```application.py```
   - ```requirements.txt```
3. AWS Beanstalk -> N. Virginia (us-east-1) -> Cdg-4-env -> Upload and deploy

