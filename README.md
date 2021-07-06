# Make things faster

Use the lightning resource provider to get push notifications for long running operations.

Instructions:

- Clone the repository
- From the root of the repository, create a virtual environment
```sh
python -m venv .env
. .env/bin/activate
pip install -r requirements.txt
pip install -e .
```

- Set the environment variable `AZURE_SUBSCRIPTION_ID` to the id of the azure subscription you want to use.

By running the script in 

```sh
python test/session/cli.py
```

you will be prompted to select running with LRP or not and which compute CRUD operation to execute. The log spew will include a "registering for notifications for \<some guid\>". By posting a message with said guid as the id, you will mark the operation as completed. You can use the script `complete.sh` to send the push notification (it takes a single argument, which is the id to mark as completed)

Note: Log level can be set to DEBUG for more information in cli.py
