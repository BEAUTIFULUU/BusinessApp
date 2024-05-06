# **BusinessApp**

BusinessApp is an application that empowers users to create their own business cards and effortlessly share their contact information with others. Additionally, users can connect with potential leads by sending and receiving contact requests.

## Tech Stack

- Django
- MySQL
- Docker
## Features

- Create and customize your business card.
- Share your contact information with ease.
- Send and receive contact requests to connect with potential leads.



## Instruction

Create Media Folder:

	- Create a folder named "media" in the root directory of the app.
	- Inside the "media" folder, create folders: "images", "qr_codes", and "vcard_files".	                                                                        
Set up Environment:

	- Create a file named dev.env based on the provided env.example.
	- Configure the environment variables according to your setup.

Set up MYSQL_USER from your dev.env in entrypoint for mysql:

    - In folder db open entrypoint.sql

    - In GRANT ALL PRIVILEGES ON *.* TO 'mysql'@'%' WITH GRANT OPTION; set 'mysql' to your MYSQL_USER from dev.env
Build Docker Compose:

	- Run "docker-compose build"
Run Docker Compose:

	- Execute "docker-compose up" to start the application.
Migrate Database:

	- Run "docker-compose run backend python manage.py migrate" to run migrations. 
Running tests:

    - Execute "docker-compose run backend pytest" to run tests.
