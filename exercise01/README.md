# Specs
- Operating System: Windows 11

- Programming language: Python, SQL, HTML + CSS

- Web-framework: Flask + Jinja2

- Run-time environment: Python 3.10

- Database: PostgreSQL Server 16.0.1

![](uml_diagram_db.png)
- Storage: SSD/Folder (File System on top of block storage)

- HTTP Paths:
    - / (GET): Optional Parameter results that stores the results from a search. Multiple results are concatenated using & repeated use of results. These values are used to populate the search section.
    - /search (GET): Expects a parameter searchValue that is populated by the browser when the search form is submitted. Uses the searchValue to query the database to find files that match the query either in the filename or in the description.
    - /upload (POST): Called by the browser when the submit button of the file upload form is pressed. Expects the file data in the http data section. Saves the file to disk.
    - /add-tag (POST): Called by the browser when the submit button of the tag upload form is pressed. Adds a tag to the database for a file.
    - /download/{filename} (GET): called by the browser when a file name is pressed that resulted from the search functionality 

# Abgabe2
1. Created a repository on docker hub called manuelhtwg/awesomefileuploader
2. We bundled the web server in a docker image called manuelhtwg/awesomefileuploader with a tag 1.0. The logic for that can be found in the file called Dockerfile.
3. Uploaded the image to docker hub.
```
docker build -t manuelhtwg/awesomefileuploader:1.0 .
docker push manuelhtwg/awesomefileuploader:1.0
```
4. Created an SSH key pair on bwcloud.
5. Created an instance using Ubuntu 22.04
6. Connected to the instance using SSH. An example command can be found below.
```
ssh -i .\bw_cloud_key.pem ubuntu@2c043adb-813b-45b7-996a-51ce39c69a41.ma.bw-cloud-instance.org	
```
7. Updated the instance using 
```
sudo apt update
sudo apt -y upgrade
```
8. Installed postgres using:
```
sudo apt install postgresql
```
9. Set the password of the user postgres to something secret and create the required database (file_uploader)
```
sudo -u postgres psql
ALTER USER postgres with encrypted password 'mysecretpassword';
CREATE DATABASE file_uploader;
```
10. Install docker on server using apt. Added user ubuntu to docker user group so that the ubuntu user can execute docker commands.

11. Created a media folder in the home directory (/home/ubuntu) that will hold the uploaded files.

12. Created a .env file containing the environment variable DATABASE_PASSWORD.

13. Used systemd to autostart our web server automatically on reboot. The installation of postgres already did that for the database.
Steps to make the webserver start by default:
```
sudo nano /etc/systemd/system/awesomefileuploader.service
```
In the text editor, add the following content to the service unit file:
```
[Unit]
Description=awesomefileuploader

[Service]
Type=exec
ExecStart=/usr/bin/docker run --rm -d --network=host --env-file /home/ubuntu/.env -v /home/ubuntu/media:/app/media manuelhtwg/awesomefileuploader:1.0
Restart=always

[Install]
WantedBy=multi-user.target
```

Save the file and exit the text editor.

Reload the systemd manager to read the new service unit:
```
sudo systemctl daemon-reload
```
Enable the service to start on boot:
```
sudo systemctl enable awesomefileuploader.service
```

14. Restart the server
```
sudo shutdown -r now
```

15. bwcloud seems to only provide a public IPv6 address. We had to add an ingress rule to the default security group with the following properties:
Direction	Ether Type	IP Protocol	Port Range	Remote IP Prefix 
Ingress	IPv6	TCP	80 (HTTP)	::/0 

16. Create a snapshot in bwcloud

17. Enjoy the server

# Abgabe3

code can be found here: [https://github.com/Manuel3567/CAD/tree/main/exercise01](https://github.com/Manuel3567/CAD/tree/main/exercise01)


for GCP deployment perform the following things:

## image creation
in GCP create a vm using CentOS 7
### local ssh setup
```
ssh-keygen
ssh manuel@publicIP
```
### commands on gcp vm
```
sudo yum -y update
sudo yum -y install docker

sudo systemctl enable docker
sudo groupadd docker
sudo usermod -aG docker -a $USER
sudo systemctl restart docker
sudo shutdown -r now
```
wait for vm restart and connect via ssh again then continue with the following commands
```
sudo sh -c 'cat << EOF > /etc/systemd/system/awesomefileuploader.service
[Unit]
Description=awesomefileuploader
After=docker.service
Wants=docker.service

[Service]
Type=notify
ExecStartPre=/usr/bin/docker run -d --network=host --env-file /home/manuel/.env manuelhtwg/awesomefileuploader:latest flask init-db
ExecStart=/usr/bin/docker run -d --network=host --env-file /home/manuel/.env manuelhtwg/awesomefileuploader:latest
Restart=always
NotifyAccess=all
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
EOF'

sudo systemctl daemon-reload
sudo systemctl enable awesomefileuploader.service
```
create an image in gcp called fileuploaderimg
## infrastructure deployment
```
cd infrastructure
terraform apply -var-file variables.tfvars
```

## infrastructure destruction
```
cd infrastructure
terraform destroy -var-file variables.tfvars
```
