# Scraping Hotels from classement.atout-france.fr

This tutorial guides you through using a Python script to scrape hotel information listed on the website `classement.atout-france.fr`.

## Prerequisites

Before you begin, ensure that you have Python 3 installed on your computer. You can download Python from the official website: [Python Downloads](https://www.python.org/downloads/)

## Getting Started

1. Open a terminal or command prompt.

2. If you want to clone the repository to a specific location, create a folder (replace `~/your/path/repos` with your desired path):
   
   ```bash
   mkdir ~/your/path/repos
    ```
   
3. Navigate to the folder
   ``` bash
   cd ~/your/path/repos
    ```
   
4. Clone the repository containing the script
    ``` bash
    git clone https://github.com/SamAmann/scraping-classement-atout-france.git
    ```
    
5. Navigate into the cloned folder
    ``` bash
    cd ./scraping-classement-atout-france
    ```

6. Install the required Python packages by running
    ``` bash
    pip install -r requirements.txt
    ```

## Running the script

``` bash
python atout_france.py
```

## Thank you note
A massive thanks to [Antoine Paix](https://github.com/AntoinePaix/scraping-classement-atout-france) for the inspiration script.
