""" 
Somayya Elmoghazy, 100875387
For this code, I followed the tutorial on https://www.youtube.com/watch?v=71EU8gnZqZQ  for login and authentication and customized it to my application
For image upload to Amazon S3 bucket and display on the webpage, I followed the tutorial on https://www.youtube.com/watch?v=5q7FtT_DyME&t=200s, https://www.youtube.com/watch?v=EvHltGpbSqo&t=420s and https://github.com/willwebberley/FlaskDirectUploader 
To run this code 


 """

from flask import Flask, render_template, url_for, redirect, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
import requests
import boto3
import os, json
from google.cloud import vision
from google.cloud.vision_v1 import types
import folium


application= Flask(__name__)
app=application

#Amazon s3 bucket for uploaded images. It's already authenticated on Heroku and can be locally authenticated using AWS CLI. Replace abuck4me with the name of your bucket.
s3 = boto3.client('s3')
BUCKET_NAME='abuck4me'

#You should include the .json file containing the API keys for google vision in place of keyFile.json'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'keyFile.json'


#database for users (username, email, password)
application.config['SQLALCHEMY_DATABASE_URI']='sqlite:///database.db'
# Define secret key to enable session
application.config['SECRET_KEY']='secretkey'
# I used a local library for login information and passwords are encrypted using Bcrypt
db = SQLAlchemy(application)
bcrypt=Bcrypt(application)
application.app_context().push()

login_manager = LoginManager() #allows Flask and login app to work together
login_manager.init_app(application)
login_manager.login_view = 'login'


#reload objects from user ids
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id=db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(20),nullable=False, unique=True)
    email=db.Column(db.String(40),nullable=False)
    password=db.Column(db.String(80),nullable=False)

# Registeration form for entering username, email and password. 
# It validates that the username is unique before registeration
class RegisterationForm(FlaskForm):
    username=StringField(validators=[InputRequired(), Length(min=4,max=20)], render_kw={"placeholder": "Username"})
    email=StringField(validators=[InputRequired(), Length(min=10,max=40)], render_kw={"placeholder": "Email"})
    password=PasswordField(validators=[InputRequired(), Length(min=4,max=20)], render_kw={"placeholder": "Password"})
    submit=SubmitField("Register")
    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username=username.data).first()
        if existing_user_username:
            raise ValidationError('That username already exists.')


# Login form for entering username and password
class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    #email=StringField(validators=[InputRequired(), Length(min=10,max=40)], render_kw={"placeholder": "Email"})

    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField('Login')


#home page diplaying home.html when the application starts up. The user has to login to get to any of the other services.
@application.route('/')
@login_required
def home():
    return render_template('home.html')

#Route for login page. 
#It renders the login.html template passing the LoginForm to it, and authenitcates the username and password entered.
#When login is successful, the application notfies the user through an email message sent using send_simple_message and directs to 'upload' page 
@application.route('/login', methods=['GET', 'POST'])
def login():
    form=LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                send_simple_message(user.email, "Successfully logged in")
                login_user(user)
                return render_template('upload.html')

    return render_template('login.html',form=form)

#Route for Registeration page. It renders the register.html template passing the RegisterationForm to it, and validates the username, email and password entered.
#If registeration is successful, it redirects to login page
@application.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, email=form.email.data,password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

#Route for upload page that uses 'upload.html' template. 
#If file is chosen, it uploads it to the s3 bucket and redirects to display_image page to display the uploaded image
@application.route('/upload', methods=['POST','GET'])
def upload():
    file = request.files['file']

    if file:
        filename = secure_filename(file.filename)
        file.save(filename)
        s3.upload_file(filename, BUCKET_NAME, filename)
        os.remove(filename)
      
        return redirect(url_for('display_image', filename=filename))
    else:
        return 'No file uploaded.'
        

#Route for display image page. It takes the filename from the previous view to generate a presigned request from the s3 bucket and get the image url to display it on the webpage.
#It then creats a Google Vision API client using the url and uses the landmark detection model to find the name and location.
#If landmark is successfuly detected, it displays the name and coordinates to the user. 
#If landmark isn't detected, a "NOT FOUND" message is printed
#If the user clicks on the "show directions" button, they are redirected to the maps view showing a pinned location of the landmark
@application.route('/<filename>',methods=['POST','GET'])
def display_image(filename):
    
        try:
            url = s3.generate_presigned_url('get_object', Params={'Bucket': BUCKET_NAME, 'Key': filename}, ExpiresIn=600)
            #print(url)
            client = vision.ImageAnnotatorClient()
            # Create a Vision API image object with the image URL as the source
            image = types.Image()
            image.source.image_uri = url
            # Perform landmark detection on the image
            response = client.landmark_detection(image=image)
            landmarks = response.landmark_annotations
            if landmarks:
                landmark_name = landmarks[0].description
                landmark_location = landmarks[0].locations[0].lat_lng
                if "directions" in request.form:
                         return redirect(url_for('get_direction', lat=landmark_location.latitude, lng=landmark_location.longitude))
             
                return render_template('display.html', url=url, landmark_name=landmark_name, landmark_location=landmark_location)
            else:
                return render_template('display.html', url=url, landmark_name="NOT FOUND", landmark_location="NOT FOUND")
 
        except Exception as e:
            print(e)
            return "Error: {}".format(str(e))


#Route for map view
#It gets the latitude and longitude of the landmark from the previous view and renders the 'map.html' view
#Folium library is used to pin the location on the map
#The Marker() functin creates a popup page of the map and saves it in 'map.html'

@application.route('/directions', methods=['POST','GET'])
def get_direction():
    lat=request.args.get('lat')
    lng =request.args.get('lng')
    m=folium.Map(location= (lat, lng), zoom_start=12)
    
    folium.Marker( [lat, lng], popup="<h1> Distination</h1>").add_to(m)
    m. save('templates/map.html')


    return render_template('map.html')


#Route for logout which redirects back to login page.
@application.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

#Function to send notfication emails that takes the user's email and the message contents to send to the user.
#It uses mailgun API. A mailgun api key is required for authenitcation in the auth parameter. 
#Domain name is emails.studio (can be replaced with any domain name as long as the necessary configurations are added to mailgun account)
#Default email of the system is mailgun@emails.studio
#You need to replace "emails.studio" in the first argument link with your domain name 

def send_simple_message(email, msg):
	return requests.post("https://api.mailgun.net/v3/emails.studio/messages",
		auth=("api", "API-KEY"),
		data={"from": "mailgun@emails.studio",
			"to": [email, "mailgun@emails.sudio"],
			"subject": "Application Message",
			"text": msg})