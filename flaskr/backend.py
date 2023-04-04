# TODO(Project 1): Implement Backend according to the requirements.
from flask import Blueprint, request, Flask, render_template, session
from flask import request, Flask
from google.cloud import storage
import hashlib
from io import BytesIO
import urllib, base64

client = storage.Client()


class Backend:
    # class Backend holds the method to interact with the GSC, thus we initialize the bucket & storage client needed to access the correct blobs
    def __init__(self, bucket_name):
        self.bucket_name = bucket_name
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(bucket_name)

    def get_wiki_page(self, name):
        blob = self.bucket.blob(name)  #search for th page with the given name
        if blob.exists():
            return blob.download_as_string(
            )  #if the page exists return the string
        else:
            return None  #else, return None

    def get_all_page_names(self):
        blobs = self.storage_client.list_blobs(
            self.bucket_name)  #list all pages
        pages = {}  #empty dict
        for blob in blobs:  #read each blob
            if blob.content_type != 'image':  #if is not an image
                pages[blob.name] = blob  #save it in a dictionary
        return pages  #return all the pages

    def upload(self, page_name, page):
        blob = self.bucket.blob(page_name)  # get blob based on page_name
        with blob.open("wb") as f:  # write page contents to blob in cloud
            if type(page) is bytes:
                f.write(page)
            else:
                f.write(page.read())

    def sign_up(self, user_name, pwd):
        # get username, password from user, salt for hashing
        name = user_name
        password = pwd
        salt = "5gz"

        # Adding salt at the last of the password
        dataBase_password = password + salt
        # Encoding the password
        hashed_password = hashlib.md5(dataBase_password.encode())

        bucket = client.bucket('userspasswords')
        blob = bucket.blob(name)

        #Adds the encoded passsword to the created user blob
        with blob.open("w") as f:
            f.write(f"{hashed_password.hexdigest()}")

    def sign_in(self, user_name, pwd):
        # get username, password from user, salt for hashing
        username = user_name
        password = pwd
        salt = "5gz"

        # Adding salt at the last of the password
        dataBase_password = password + salt
        # encoding the password
        hashed_password = hashlib.md5(dataBase_password.encode())

        bucket = client.bucket('userspasswords')
        blob = bucket.blob(username)

        #checks if the entered username exsists in the bucket
        if not blob.exists():
            return 'Invalid User'
        else:
            with blob.open("r") as f:
                psw = f.read()  # reads the stored password from the blob
            if hashed_password.hexdigest() != psw:
                return 'Invalid Password'
            else:
                return username

    def get_image(self, image_name, blob_param=None):
        # get blob based on image name
        blobs = self.storage_client.list_blobs(self.bucket_name)

        # function decodes image to readable version to display on html page
        def decode_img(image):
            img_string = base64.b64encode(image.read())
            img = 'data:image/png;base64,' + urllib.parse.quote(img_string)
            return img

        # if (optional) blob supplied, decode image directly
        if blob_param:
            return decode_img(blob_param)

        # if not, find blob that matches image name and return decoded image
        for blob in blobs:
            if blob.name == image_name:
                with blob.open("rb") as b:
                    return decode_img(b)

    def sanitize(self, page):
        """ Uses the bleach library to clean the uploaded html based on the allowed tags and attributes and converts the text
        links to safe links and then upload to cloud

        Args:
            page: HTML file to sanitize
        Returns: Sanitized HTML file
        """
        import bleach
        allowed_tags = [
            'a', 'abbr', 'acronym', 'b', 'blockquote', 'br', 'code', 'dd',
            'del', 'div', 'dl', 'dt', 'em', 'h1', 'h2', 'h3', 'hr', 'i', 'img',
            'li', 'ol', 'p', 'pre', 's', 'strong', 'sub', 'sup', 'table',
            'tbody', 'td', 'th', 'thead', 'tr', 'ul'
        ]
        allowed_attrs = {
            '*': ['class'],
            'a': ['href', 'rel'],
            'img': ['src', 'alt']
        }
        if not type(page) is str:
            page = page.read().decode('utf-8')
        sanitized = bleach.clean(page,
                                 tags=allowed_tags,
                                 attributes=allowed_attrs).encode('utf-8')
        return sanitized
