# Space-Engineers-CSV-to-Mod-List-Maker
This takes a CSV (see example Google Sheet for exmaple) and conerts it to an xml formated Mod List for Space Engineers

# Example Spreadsheet - Make sure to copy this, and edit. Also when you download it, save it as a .csv file
<https://docs.google.com/spreadsheets/d/1tZrctJX1qepEPEoaRccc63lDXFgkYw_ZaZJ4a8JWtd4/edit?usp=sharing>

# Requierments
Python - Thats all you need.

# Onetime Setup
install libraries
```
pip install pandas networkx
```

# How to Run
1) make sure you save the csv file in the same root as your the python script. I would name it something simple like mods.csv
2) In terminal, navigate to the folder:
```
cd path\to\your\folder
```
3) Then run:
```
python csv‑to‑mods‑xml.py mods.csv mods.xml
```

# Breakdown

Argument 1: Required "mods.csv" - this is the name of the csv file

Argument 2: Required "mods.xml" - this is the output name of the xml file that will be created

Optional flag: Optional "--deps-first" - this will instead of the default behavior bvy listing dependencies last, it will list them first.