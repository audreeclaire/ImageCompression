from flask import Flask, Response, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import os
import sys
import numpy as np
import sqlite3
from PIL import Image
import shutil
from functools import wraps

key=27

app = Flask(__name__)
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png']

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 'admin' and password == 'shopify'

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'You must verify your credentials to access this feature.\n'
    'Go back and try again.', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def encryption(image):
    image = bytearray(image)
    for index, values in enumerate(image): 
        image[index] = values ^ key 
    return image


def writeTofile(data, filename):
    #convert binary data back to image and save it
    with open(filename, 'wb') as file:
        file.write(data)
    print("Stored blob data into: ", filename, "\n")

def readBlobData():
    try:
        
        conn = sqlite3.connect('images.db')
        cursor = conn.cursor()
        print("Connected to SQLite")
        #os.mkdir()

        cursor.execute("""SELECT * from all_images""")
        record = cursor.fetchall()
        for row in record:
            name  = row[0]
            photo = row[1]
            

            print("Storing photo on disk \n")
            retrievedImagesPath = "./retrievedImages/" + name
            
            #DECRYPT
            photo = encryption(photo)
            writeTofile(photo, retrievedImagesPath)

        cursor.close()

    except sqlite3.Error as error:
        print("Failed to read data from SQLite table", error)
        
    finally:
        if (conn):
            conn.close()
            print("sqlite connection is closed")


def convertToBinaryData(filename):
    #convert photo to binary and return data
    with open(filename, 'rb') as file:
        blobData = file.read()
    return blobData
        
def insertBLOB(name,photo):
    try:
        conn = sqlite3.connect('images.db')
        cursor = conn.cursor()
        print("Connected to SQLite")
        sqlite_insert_blob_query = """ INSERT INTO all_images (name,image) VALUES (?,?)"""
        
        
        newImage = convertToBinaryData(photo)
        #ENCRYPT
        newImage = encryption(newImage)
        
        data_tuple = (name,(newImage))
        cursor.execute(sqlite_insert_blob_query, data_tuple)
        conn.commit()
        print("success")
        cursor.close()
    
    except sqlite3.Error as error:
        print("Failed to put data into SQLite table", error)
        
    finally:
            if(conn):
                conn.close()
                print("connection closed")

def makeDirectory():
    try:
        os.makedirs('retrievedImages')
    except:
        print("Error fetching images.")

def compress():
    #recover photos from database and zip
    makeDirectory()
    readBlobData()
    shutil.make_archive('./my_photos', 'zip',"./retrievedImages")
    shutil.rmtree('./retrievedImages')



def load_sample_data():
    i = 1
    while i <= 5:
        name = "photo" + str(i) + ".jpeg"
        location =  "./sampleImages/" + name
        insertBLOB(name,location)
        i += 1
    

#HOME PAGE
@app.route('/')
def index():
    return render_template('index.html')

#HOME - COMPRESS BTN
@app.route('/', methods=['POST'])
@requires_auth
def index_page(): 
    compress()
    return redirect(url_for('index'))
    
#ADD PAGE
@app.route('/addImage/')
@requires_auth
def addImagePage():   
    try:
        conn = sqlite3.connect('images.db')
        cursor =conn.execute('SELECT name, image FROM all_images')
        photos = cursor.fetchall()
        #convert photos back from binary
    except sqlite3.Error as error:
        print("Error fetching images.", error)
        
    finally:
        if(conn):
            conn.close()
            print("connection closed")
            return render_template('addImage.html', photos=photos)

#Add image btn
@app.route('/addImage/', methods=['POST'])
def add_to_collection():
    uploaded_files = request.files.getlist("addedimages")
    for file in uploaded_files:
        if file.filename != '':
        
            #COMPRESS AND SAVE TO DATABASE AS BINARY
            file.save(file.filename)
            file = Image.open(file.filename)
            file.save(file.filename, optimize = True, quality = 20)
       
            insertBLOB(file.filename, file.filename)
            #delete source file
            os.remove(file.filename)
            
    return redirect(url_for('addImagePage'))    
    
@app.route('/deleteImage/')
@requires_auth
def deleteImagePage():
    try:
        conn = sqlite3.connect('images.db')
        cursor = conn.execute('SELECT name,image FROM all_images')
        photos = cursor.fetchall()
        conn.commit()
    
    except sqlite3.Error as error:
        print("Error fetching images.", error)
        
    finally:
        if(conn):
            conn.close()
            print("connection closed")
            return render_template('deleteImage.html', photos=photos)

@app.route('/deleteImage/', methods=['POST'])
def delete_from_collection():   
    try:
        imageId = request.form.get('delete')
        conn = sqlite3.connect('images.db')
        cursor = conn.cursor()
        
        if(imageId == "Clear All"):
            cursor.execute("""DELETE FROM all_images""")
        else:
            cursor.execute("""DELETE FROM all_images WHERE name = ? """, (imageId,))
            
        conn.commit()
        cursor.close()
        
    except sqlite3.Error as error:
        print("Error deleting images.", error)   
        
    finally:
        if(conn):
            conn.close()
            print("connection closed")
            return redirect(url_for('deleteImagePage'))   
 

    
#INITIALIZE
if __name__ == '__main__':
    #reset table in database images.db
    try:
        conn = sqlite3.connect('images.db')
        cursor = conn.cursor()
        cursor.execute(""" DROP TABLE IF EXISTS all_images""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS all_images (name TEXT, image BLOP)""")
        conn.commit()
        cursor.close()
        
    except sqlite3.Error as error:
        print("Error creating table.", error)   
    
    finally:
        if(conn):
            conn.close()
            print("connection closed")
            load_sample_data()
            app.run(debug=True)
