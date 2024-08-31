# General
This repo contains utilities used to interact with the REST API of our CDG server, as presented in 09/05/2024 meeting.

The directories [BGU](BGU), [Fujitsu-1](Fujitsu-1), [Fujitsu-2](Fujitsu-1) contain the datasets collected on 15/08/2023, 16/02/2024, and 04/03/2024.
They also contain the corresponding `servers.csv` and `solution.csv` files, which are required by the API.

# Usage

## Python:
Download [Example-usage-Python.ipynb](Example-usage-Python.ipynb).

Use any IDE that supports Python Jupyter Notebooks (My recommendation: Visual Studio Code).

## Linux:
Download [Example-usage-Linux.sh](Example-usage-Linux.sh).

jq must be installed to support JSON parsing:
```
apt install -y jq
```
You might need to convert the script to linux file format (LF as line endings):
```
apt install -y dos2unix
dos2unix Example-usage-Linux.sh
```
Then run with:
```
chmod +x Example-usage-Linux.sh
./Example-usage-Linux.sh
```

## Windows:
Download [Example-usage-Win.ps1](Example-usage-Win.ps1).

Run from inside powershell shell:
```
Example-usage-Win.ps1
```
Or invoke Powershell from CMD:
```
Powershell -File Example-usage-Win.ps1
```
You might need to allow running scripts.
Using Powershell as administrator, run:
```
Set-ExecutionPolicy -ExecutionPolicy Unrestricted -Scope Process
```
Or, CMD one-liner:
```
Powershell -Command "Set-ExecutionPolicy -ExecutionPolicy Unrestricted -Scope Process; & .\Example-usage-Win.ps1"
```
