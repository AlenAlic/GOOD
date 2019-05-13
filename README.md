# Graduation Overview and Output for Dancing (GOOD) System

Web based grading system for Ballroom dancing graduations.

## Installation (Ubuntu or Raspbian)
This will assume a fresh installation of Ubuntu 18.04. The installation on Raspbian is similar.

Commands are for both systems, unless stated otherwise.

Before we start installing the system, start with the following commands to update the system:

    sudo apt -y update
    sudo apt -y upgrade

On Ubuntu, you might need to update your drivers as well:

    sudo ubuntu-drivers autoinstall

### Base dependencies
First, we will need install a few base dependencies:

**Ubuntu**

    sudo apt -y install python3 python3-venv python3-dev mysql-server supervisor nginx git

**Raspbian**

    sudo apt -y install python3 python3-venv python3-dev mariadb-server supervisor nginx git libatlas-base-dev

### Installing the application
Install the application through git:

    # clone the repository
    git clone https://github.com/AlenAlic/GOOD
    cd GOOD

#### Dependencies
Create a virtualenv and activate it. Then install all the package dependencies in the virtualenv:

    python3 -m venv venv
    source venv/bin/activate
    pip install pip --upgrade
    pip install setuptools --upgrade
    pip install -r requirements.txt
    pip install gunicorn

#### Config
Create a file named the config.py file in the instance folder.

    sudo nano instance/config.py

The file should contain the following variables:

    ENV = 'production'
    DEBUG = False
    SECRET_KEY = 'random_string'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://good:<db_password>@localhost:3306/good'
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = False

You can create the SECRET_KEY for the website, and password for the MySQL database using the following command:

    python3 -c "import uuid; print(uuid.uuid4().hex)"

Save the config file (Ctrl+x, y, Enter).

Finally, you need to set the FLASK_APP environment variable in the system:

    export FLASK_APP=run.py
    echo "export FLASK_APP=run.py" >> ~/.profile
The second line sets it so that the command is automatically run when you log in.

### Database
Enter the database with the following command:

    sudo mysql

Create a new database called **good**, along with a user with the same name, that has full access to the database.

    create database good character set utf8mb4 collate utf8mb4_unicode_ci;
    create user 'good'@'localhost' identified by '<db-password>';
    grant all privileges on good.* to 'good'@'localhost';
    flush privileges;
    quit;

Make sure you replace <db-password> with the password that was set in the *config.py* file.

Next, we need to initialize the database structure:

    flask db upgrade

### Set up admin account for website
Before you can log in to the site, you will need to create the admin account through the shell:

    flask shell
    create_admin('admin_password')
    exit()

You can log in with the username *admin*.

### Gunicorn
Gunicorn is a pure Python web server that will be used in stead of the built in Flask server. Though in stead of running gunicorn directly, we'll let it run through the supervisor package. Supervisor will then have it running in the background instead. Should something happen to the server, or if the machine is rebooted, the server will be restarted on its own.

Create a file called *good.conf* in the folder */etc/supervisor/conf.d/*

    sudo nano /etc/supervisor/conf.d/good.conf

Copy the data from below into that file and replace *<username>* with the username of the machine account.

    [program:good]
    command=/home/<username>/GOOD/venv/bin/gunicorn -b 127.0.0.1:8001 --worker-class eventlet -w 1 run:app
    directory=/home/<username>/GOOD
    user=<username>
    autostart=true
    autorestart=true
    stopasgroup=true
    killasgroup=true

After saving this file, reload the supervisor.

    sudo supervisorctl reload

The gunicorn web server should now be up and running on localhost:8001.

### Nginx
Nginx is used to serve the pages that are generated by Gunicorn to the outside world.

After installation, Nginx already comes with a test site. remove it first:

    sudo rm /etc/nginx/sites-enabled/default

 Create a file called *dance. in the folder */etc/nginx/sites-available/*

    sudo nano /etc/nginx/sites-available/dance

Copy the data from below into that file and replace *<username>* with the username of the machine account.

    server {
        listen 80;
        server_name _;

        location / {
            proxy_pass http://127.0.0.1:8001;
            proxy_redirect off;
            proxy_set_header Host $http_host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }

        location /static {
            alias /home/<username>/GOOD/GOOD/static;
            expires 1d;
        }
    }

Next, create a symlink for this file in the */etc/nginx/sites-enabled/* folder.

    sudo ln -s /etc/nginx/sites-available/good /etc/nginx/sites-enabled/

After creating the symlink, reload nginx:

    sudo service nginx reload

### Congratulations!

The GOOD system should be available on the local network through the local ip address of the machine you're on.

### Raspberry Pi local WiFi network (optional)
If you're installing this on a Raspberry Pi, you can use the Pi to host the WiFi network for others to connect to as well. Begin by installing Dnsmasq and hostapd.

    sudo apt -y install hostapd dnsmasq
After installing them, stop the newly installed programs.

    sudo systemctl stop hostapd
    sudo systemctl stop dnsmasq
First, configure the device to use a static IP address over WiFi, by opening the following file:

    sudo nano /etc/dhcpcd.conf
Then past the following into the file. This will give the Pi the IP address 192.168.4.1, and will tell devices connected to the network to use the Pi as a DNS.

    interface wlan0
    static ip_address=192.168.4.1/24
    static domain_name_servers=192.168.4.1
Next, restart program.

    sudo systemctl restart dhcpcd
Rename the old DHCP configuration file (for save keeping).

    sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
Create a new config file.

    sudo nano /etc/dnsmasq.conf
Copy the following data into the new file. For the WiFi connection, we are going to provide IP addresses between 192.168.4.2 and 192.168.4.20, with a lease time of 24 hours. Additionally, we will use a different file to create domain names for the Pi (only for devices connected to this network).

    interface=wlan0
    dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
    addn-hosts=/etc/dnsmasq_hosts.conf
Open file that will contain the domain names for the Pi.

    sudo nano /etc/dnsmasq_hosts.conf
And add the domain names to the file as shown below.

    192.168.4.1     <custom_domain_name1> <custom_domain_name2> etc
Next, open the hostapd configuration file.

    sudo nano /etc/hostapd/hostapd.conf
Copy the data from below into that file and replace *<network_name>* with the name of the network, and *<network_password>* with the password.

    interface=wlan0
    driver=nl80211
    
    ieee80211d=1
    country_code=NL
    ieee80211n=1
    
    hw_mode=g
    channel=7
    wmm_enabled=0
    macaddr_acl=0
    ignore_broadcast_ssid=0
    
    auth_algs=1
    wpa=2
    wpa_key_mgmt=WPA-PSK
    wpa_pairwise=TKIP
    rsn_pairwise=CCMP
    
    # Network name
    ssid=<network_name>
    # Password
    wpa_passphrase=<network_password>
Open the default hostapd file.

    sudo nano /etc/default/hostapd
Find *DAEMON_CONF=""* and replace it with the following:

    DAEMON_CONF="/etc/hostapd/hostapd.conf"
Open the following file:

    sudo nano /etc/init.d/hostapd
Find *DAEMON_CONF=""* and replace it with the following:

    DAEMON_CONF=/etc/hostapd/hostapd.conf
Finally, restart the systems.

    sudo service dnsmasq start
    sudo systemctl unmask hostapd
    sudo systemctl enable hostapd
    sudo systemctl start hostapd
