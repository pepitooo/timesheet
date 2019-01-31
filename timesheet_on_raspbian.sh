#!/bin/sh

sudo apt update
sudo apt upgrade -y
sudo apt install -y supervisor nginx python3 sqlite3 virtualenv git npm
sudo npm install -g bower

cd
git clone https://github.com/pepitooo/timesheet.git
cd timesheet
virtualenv -p python3
source bin/activate
pip install -r requirements.txt 
cd static
bower install
 

cd /etc/supervisor/conf.d/
sudo ln -s /home/pi/timesheet/config_files/supervisor timesheet.conf
cd /etc/nginx/sites-available
sudo ln -s /home/pi/timesheet/config_files/config_files/nginx timesheet
sudo ln -s timesheet ../sites-enabled
sudo rm /etc/nginx/sites-enabled/default

sudo cp /home/pi/timesheet/config_files/cron /etc/cron.d/timesheet
sudo chmod +x /etc/cron.d/timesheet
