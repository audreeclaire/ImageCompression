# ImageRepository

---
## Overview

A Flask web application that allows user to compress image files and store them securely in a SQLite3 database. Images from the user are converted to binary data and encrypted using simple mathematical encryption before being added to the database. 

---

## Usage

run `python3 server.py` from the command line and open a web browser at http://localhost:5000

The add, delete, and compress features require user authentication. The username is set to 'admin' and the password is 'shopify'.

---

## Features

ADD: The user can upload single or bulk image files which will then be compressed and encrypted before being added to the database.

DELETE: The user can remove single or all images currently in the database.

SAVE .ZIP: The images from the database will be decrypted and saved as my_photos.zip to the disk.
