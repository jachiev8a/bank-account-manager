# Bank-Account-Manager

## ! WARNING !
only available for PDF files from Mexico bank accounts

## Description
This is a simple bank account manager that allows you to parse PDFs from your bank and get a summary of your account.

Or keep them organized by date.

## Installation

This project is designed to work with Python 3.12.x and requires the installation of several libraries. It is recommended to use a virtual environment to avoid conflicts with other projects.
You can use `venv` or `virtualenv` to create a virtual environment. Here is how you can do it:
```bash
# Create a virtual environment
python -m venv .venv
# Activate the virtual environment
# On Windows
.venv\Scripts\activate
# On macOS/Linux
source .venv/bin/activate
```

After activating the virtual environment, you can install the required libraries using pip.
```bash
pip install -r requirements.txt
```

Also, additional software is required to ba able to parse PDF files as images, such as `tesseract-ocr`. You can install it using the following commands:
```bash
sudo apt install tesseract-ocr
sudo apt install libtesseract-dev
```


## How to use it

1. Configure the project at the `config.yaml` file
2. Configure the path for `directory_list_to_look_for_pdfs` to set the location of the PDFs
3. Run the script
```bash
python main.py
```
