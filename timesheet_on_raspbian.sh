#!/bin/sh

sudo apt update
sudo apt upgrade -y
sudo apt install -y supervisor nginx python3 sqlite3 virtualenv git npm
sudo npm install -g bower

cd
git clone https://github.com/pepitooo/timesheet.git
cd timesheet
virtualenv -p python3 .
. bin/activate
pip install -r requirements.txt 
cd static
bower install
 
sudo cp /home/pi/timesheet/config_files/supervisor timesheet.conf
sudo cp /home/pi/timesheet/config_files/nginx /etc/nginx/nginx.conf
sudo cp /home/pi/timesheet/config_files/cron /etc/cron.d/timesheet
sudo chmod +x /etc/cron.d/timesheet
