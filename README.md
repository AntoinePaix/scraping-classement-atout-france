# Scraping classement.atout-france.fr

This is a python script that allows you to scrape the hotels listed on the site [classement.atout-france.fr](https://www.classement.atout-france.fr/)

## To install this script:

Install Python 3 on your computer if it is not already installed. You can download Python from the official website: https://www.python.org/downloads/

Open a terminal or command prompt and navigate where you want to clone the repo.
``` bash
# if folder does not exist
mkdir ~/your/path/repos

# if folder already exists
cd ~/your/path/repos
```
Still using the terminal, clone or download the repository containing the script to your computer.
``` bash
git clone https://github.com/SamAmann/scraping-classement-atout-france.git
```
And then navigate in this folder
``` bash
cd ./scraping-classement-atout-france
```

Install the required Python packages by running the following command:
``` bash
pip install -r requirements.txt
```

This will install the required packages listed in the requirements.txt file.

Run the script by running the following command:
``` bash
python atout_france.py
```

This will start the script and prompt you to enter the number of pages to scrape and the file type to save the data to.

Follow the prompts to enter the desired options and wait for the script to finish running. 
The scraped data will be saved to a CSV or XLSX file in the same directory as the script.

## Thank you note
A massive thanks to [Antoine Paix](https://github.com/AntoinePaix/scraping-classement-atout-france) for the inspiration script.
