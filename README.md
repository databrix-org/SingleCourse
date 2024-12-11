# SingleCourse

SingleCourse is a web application for only one Course designed to provide a seamless experience for embeding a course in an existing LMS. It also provides functionalities to manage and access course materials efficiently. This README provides comprehensive instructions on how to deploy the application using Docker, set up Apache as a reverse proxy with Shibboleth for authentication, and configure the necessary environment on an Ubuntu VM.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Set Up Ubuntu VM](#2-set-up-ubuntu-vm)
  - [3. Create Persistent Volumes](#3-create-persistent-volumes)
- [Deploying with Docker](#deploying-with-docker)
  - [1. Install Docker and Docker Compose](#1-install-docker-and-docker-compose)
  - [2. Configure Docker Compose](#2-configure-docker-compose)
  - [3. Start the Application](#3-start-the-application)
- [Configuring Apache as a Reverse Proxy](#configuring-apache-as-a-reverse-proxy)
  - [1. Install Apache](#1-install-apache)
  - [2. Enable Required Modules](#2-enable-required-modules)
  - [3. Configure Virtual Host](#3-configure-virtual-host)
  - [4. Serve Static Files](#4-serve-static-files)
- [Setting Up Shibboleth for Authentication](#setting-up-shibboleth-for-authentication)
  - [1. Install Shibboleth](#1-install-shibboleth)
  - [2. Configure Shibboleth](#2-configure-shibboleth)
  - [3. Integrate Shibboleth with Apache](#3-integrate-shibboleth-with-apache)
- [Final Steps](#final-steps)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Prerequisites

Before you begin, ensure you have the following:

- An Ubuntu VM (18.04 LTS or later)
- Root or sudo access to the VM
- Docker installed on your local machine (if deploying remotely)

## Installation

### 1. Set Up Ubuntu VM
Ensure your Ubuntu VM is up and running. You can use platforms like AWS, Azure, or local virtualization tools such as VirtualBox.

### 2. Create Persistent Volumes
Create directories on your VM to store static and data files persistently.

```bash Copy
mkdir -p /var/singlecourse/static
mkdir -p /var/singlecourse/data
```

## Deploying with Docker
### 1. Install Docker and Docker Compose
If Docker is not already installed on your Ubuntu VM, follow the instruction to install:
[Official Instruction](https://docs.docker.com/engine/install/ubuntu/)

### 2. Configure Docker Compose
Ensure the docker-compose.yml file is properly configured to use the persistent volumes.

```yaml Copy
version: '3.8'

services:
  web:
    image: guyq1997/singlecourse:latest
    command: /app/docker-entrypoint.sh
    ports:
      - "8000:8000"
    volumes:
      - /var/singlecourse/static:/app/static
      - /var/singlecourse/data:/app/data
    restart: always
```

### 3. Start the Application
Run the following command to build and start the Docker containers:

```bash Copy
sudo docker-compose up -d
# Verify that the containers are running
sudo docker-compose ps
```

## Configuring Apache as a Reverse Proxy
### 1. Install Apache
Install Apache on your Ubuntu VM:

```bash Copy
sudo apt update
sudo apt install -y apache2
```

### 2. Enable Required Modules
Enable the necessary Apache modules for proxying and serving static files:

```bash Copy
sudo a2enmod proxy
sudo a2enmod proxy_http
sudo a2enmod headers
sudo a2enmod rewrite
sudo a2enmod ssl
sudo a2enmod proxy_balancer
sudo a2enmod lbmethod_byrequests
```

### 3. Configure Virtual Host
Create a new Apache virtual host configuration file:
```bash Copy
sudo nano /etc/apache2/sites-available/singlecourse.conf
```
Add the following configuration:
```apache Copy
<VirtualHost *:80>
    ServerName yourdomain.com

    # Redirect all HTTP requests to HTTPS
    Redirect permanent / https://yourdomain.com/

</VirtualHost>

<VirtualHost *:443>
    ServerName yourdomain.com

    # SSL Configuration
    SSLEngine on
    SSLCertificateFile /etc/ssl/certs/your_cert.pem
    SSLCertificateKeyFile /etc/ssl/private/your_key.pem

    # Proxy settings
    ProxyPreserveHost On
    ProxyPass / http://localhost:8000/
    ProxyPassReverse / http://localhost:8000/

    # Serve static files
    Alias /static /var/singlecourse/static
    <Directory /var/singlecourse/static>
        Require all granted
    </Directory>

    # Shibboleth Authentication
    <Location />
        AuthType shibboleth
        ShibRequestSetting requireSession 1
        Require valid-user
    </Location>

    ErrorLog ${APACHE_LOG_DIR}/singlecourse_error.log
    CustomLog ${APACHE_LOG_DIR}/singlecourse_access.log combined
</VirtualHost>
```
Note: Replace yourdomain.com, /etc/ssl/certs/your_cert.pem, and /etc/ssl/private/your_key.pem with your actual domain and SSL certificate paths.

### 4. Enable the Virtual Host
Enable the new site and disable the default site:

```bash Copy
sudo a2ensite singlecourse.conf
sudo a2dissite 000-default.conf
```
Reload Apache to apply the changes:
```bash Copy
sudo systemctl reload apache2
```
## Setting Up Shibboleth for Authentication
### 1. Install Shibboleth
Install Shibboleth Service Provider on your Ubuntu VM:
```bash Copy
sudo apt update
sudo apt install -y libapache2-mod-shib2 shibboleth-sp2-common
```
### 2. Configure Shibboleth
Edit the Shibboleth configuration file:
```bash Copy
sudo nano /etc/shibboleth/shibboleth2.xml
```
Ensure the configuration aligns with your Identity Provider (IdP) settings. You may need to obtain metadata from your IdP and update the <SSO> and <MetadataProvider> sections accordingly.

### 3. Integrate Shibboleth with Apache
After configuring Shibboleth, restart the services:
```bash Copy
sudo systemctl restart apache2
sudo systemctl restart shibd
```
Ensure that Shibboleth is correctly integrated by accessing your application URL in the browser. You should be prompted to authenticate via your configured IdP.

## Final Steps
Ensure Firewall Rules: Make sure that ports 80 and 443 are open.
```bash Copy
sudo ufw allow 'Apache Full'
```
Verify Deployment: Navigate to https://yourdomain.com in your web browser. You should see the SingleCourse application, authenticated via Shibboleth, with static files served correctly.
## Troubleshooting
Docker Issues: Check Docker container logs if the application is not running as expected.
```bash Copy
sudo docker-compose logs
```
Apache Errors: Inspect Apache logs for any configuration issues.
```bash Copy
sudo tail -f /var/log/apache2/error.log
```
Shibboleth Authentication Problems: Ensure that Shibboleth is correctly configured with your IdP and that metadata is up to date.
```bash Copy
sudo tail -f /var/log/shibboleth/shibd.log
```
## License
This project is licensed under the MIT License.


