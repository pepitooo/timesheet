#!/bin/sh

sudo apt update
sudo apt upgrade -y
sudo apt install -y supervisor nginx python3 sqlite3 virtualenv git npm redis-server
sudo npm install -g bower

cd
git clone https://github.com/pepitooo/timesheet.git
cd timesheet
virtualenv -p python3 .
. bin/activate
pip install -r requirements.txt 
cd static
bower install


sudo cp /home/pi/timesheet/config_files/supervisor /etc/supervisor/conf.d/timesheet.conf
sudo cp /home/pi/timesheet/config_files/nginx /etc/nginx/nginx.conf

# cron is maybe not the best idea as it every minutes
#sudo cp /home/pi/timesheet/config_files/cron /etc/cron.d/timesheet
#sudo chmod +x /etc/cron.d/timesheet

sudo service nginx restart
sudo service supervisor restart

