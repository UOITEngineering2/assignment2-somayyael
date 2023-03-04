# Travel Guide Application

This is a simple travel guide application. We usually find pictures of places online with no information of where those places are. The aim of the application is to allow users to upload images of places and locate these places on the map. 
## Requirements

Install requirements.txt using:
pip install -r requirements.txt or pip3 install -r requirements.txt

## Testing

The application is currently up at https://enigmatic-castle-20724.herokuapp.com/ 

The application needs the following API keys to be run:
- Amazon s3 bucket authenticated either on Heroku or locally
- Google Vision API keys saved in a .json file
- mailgun API key to send notifications email
- I used my domain name "emails.studio" in this application but you can replace it with any other domain name as long as it's configured with your mailgun account

## Data
- A local database is used for authentication found in instance/database.db 
- You can create your own account in the registeration page then login using it
- All uploaded images are saved in an Amazon s3 bucket


## credits
For this code, I followed the tutorial on https://www.youtube.com/watch?v=71EU8gnZqZQ  for login and authentication and customized it to my application
For image upload to Amazon S3 bucket and display on the webpage, I followed the tutorial on https://www.youtube.com/watch?v=5q7FtT_DyME&t=200s, https://www.youtube.com/watch?v=EvHltGpbSqo&t=420s and https://github.com/willwebberley/FlaskDirectUploader 

