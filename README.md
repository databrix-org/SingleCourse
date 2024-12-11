# SingleCourse

SingleCourse is a web application for only one Course designed to provide a seamless experience for embeding a course in an existing LMS. It also provides functionalities to manage and access course materials efficiently. This README provides comprehensive instructions on how to deploy the application using Docker, set up Apache as a reverse proxy with Shibboleth for authentication, and configure the necessary environment on an Ubuntu VM.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [1. Set Up Ubuntu VM](#1-set-up-ubuntu-vm)
  - [2. Create Persistent Volumes](#2-create-persistent-volumes)
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
#Listen 80
<VirtualHost *:80>
  ServerName 1985609f-7839-4819-8840-2d38548e4ea5.ma.bw-cloud-instance.org
  Redirect / https://1985609f-7839-4819-8840-2d38548e4ea5.ma.bw-cloud-instance.org/
</VirtualHost>

#Listen 443
<VirtualHost *:443>
  ServerName 1985609f-7839-4819-8840-2d38548e4ea5.ma.bw-cloud-instance.org

  SSLProxyEngine on
  ServerSignature Off

  # Enable HTTP/2, if available
  Protocols h2 http/1.1

  # HTTP Strict Transport Security (mod_headers is required) (63072000 seconds)
  Header always set Strict-Transport-Security "max-age=63072000"
  Header set Content-Security-Policy "frame-ancestors 'self' https://1985609f-7839-4819-8840-2d38548e4ea5.ma.bw-cloud-instance.org;"
  # Configure SSL
  SSLEngine on
  SSLCertificateFile /etc/letsencrypt/live/1985609f-7839-4819-8840-2d38548e4ea5.ma.bw-cloud-instance.org/fullchain.pem
  SSLCertificateKeyFile /etc/letsencrypt/live/1985609f-7839-4819-8840-2d38548e4ea5.ma.bw-cloud-instance.org/privkey.pem
  #Include /etc/letsencrypt/options-ssl-apache.conf
  SSLOpenSSLConfCmd DHParameters /etc/ssl/certs/dhparams.pem
  # Intermediate configuration from SSL-config.mozilla.org (2022-03-03)
  SSLProtocol all -SSLv3 -TLSv1 -TLSv1.1
  SSLCipherSuite ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384
  SSLHonorCipherOrder off
  SSLSessionTickets off

  # Jupyter-collaboration URL contains %, Apache must % understand
  AllowEncodedSlashes             On
#----------------------Shibboleth-------------------------------
  UseCanonicalName          On
  Include     /etc/shibboleth-ds/shibboleth-ds.conf
  Redirect       seeother /shibboleth https://1985609f-7839-4819-8840-2d38548e4ea5.ma.bw-cloud-instance.org/Shibboleth.sso/Metadata
  RedirectMatch /start-session$ /Shibboleth.sso/Login

  <Location /Shibboleth.sso>
    AuthType None
    Require all granted
  </Location>

  <Location /shibboleth-sp>
    AuthType None
    Require all granted
  </Location>

  Alias /shibboleth-sp/main.css /usr/share/shibboleth/main.css

#----------------------static files-----------------------------
  # Alias for Static Files
  Alias /static/ /opt/SingleCourse/static_volume/
  <Directory /opt/SingleCourse/static_volume>
      Require all granted
  </Directory>

  # Alias for Media Files
  Alias /data/ /opt/SingleCourse/data_volume/
  <Directory /opt/SingleCourse/SingleCourseWebApp/data_volume>
      Require all granted
  </Directory>
#----------------------APP-------------------------------
  # APP proxy configuration
  <Location /auth>
    #AuthType shibboleth
    #ShibRequestSetting requireSession 1
    #require valid-user
    RewriteEngine On
    ProxyPreserveHost On
    ShibUseHeaders On
    # Ensure trailing slash
    # RewriteRule ^/$ /jupyter/ [R]

    ProxyPass http://193.196.55.219:8008/auth
    ProxyPassReverse http://193.196.55.219:8008/auth
  </Location>

  <Location /course>
    #AuthType shibboleth
    #ShibRequestSetting requireSession 1
    ShibUseHeaders On
    RewriteEngine On
    ProxyPreserveHost On

    # Ensure trailing slash
    # RewriteRule ^/$ /jupyter/ [R]

    ProxyPass http://193.196.55.219:8008/course
    ProxyPassReverse http://193.196.55.219:8008/course
  </Location>

  <Location />
    AuthType shibboleth
    ShibRequestSetting requireSession 1
    require valid-user
    RequestHeader set HTTP_MAIL %{mail}e env=mail
    RequestHeader set HTTP_GIVENNAME %{givenName}e env=givenName
    RequestHeader set HTTP_SN %{sn}e env=sn
    RequestHeader set HTTP_UID %{uid}e env=uid
  </Location>

  <Location /admin>

    ShibRequestSetting requireSession off
    ShibUseHeaders On
    RewriteEngine On
    ProxyPreserveHost On


    ProxyPass http://193.196.55.219:8008/admin
    ProxyPassReverse http://193.196.55.219:8008/admin
  </Location>

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
apt install libapache2-mod-shib ntp
 
wget --no-check-certificate https://shibboleth.net/downloads/embedded-discovery-service/latest/shibboleth-embedded-ds-1.3.0.tar.gz && \
tar -xzf shibboleth-embedded-ds-1.3.0.tar.gz && \
cd shibboleth-embedded-ds-1.3.0 && \
make install
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


