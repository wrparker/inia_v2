echo "Beginning Repo Pull"
sudo git pull

echo "Changing to current user"
sudo chown -R $USER:$USER *
sudo chown -R $USER:$USER .*

echo "Using current user to run setup-env (so virtualenv available)"
bash setup_env.bash

source .virtualenv/bin/activate
echo "Collecting Static Files"
python3 proj/manage.py collectstatic --no-input

echo "Performing any Migrations.."
python3 proj/manage.py migrate
deactivate


echo "Restore UWSGI permissions"
sudo chown -R uwsgi:uwsgi *
sudo chown -R uwsgi:uwsgi .*

echo "Restarting NGINX and uwsgi"
sudo systemctl restart nginx && sudo systemctl restart uwsgi


