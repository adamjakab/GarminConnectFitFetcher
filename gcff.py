from datetime import datetime
import logging
import json
import os
import argparse
from datetime import timedelta

from dateutil import tz
from garminexport.retryer import Retryer, ExponentialBackoffDelayStrategy, \
    MaxRetriesStopStrategy
from garminexport.garminclient import GarminClient
import garminexport.backup

log = logging.getLogger(__name__)
logging.getLogger("requests").setLevel(logging.DEBUG)
logging.getLogger("garminexport").setLevel(logging.DEBUG)


def gcff(config_file):
    config = {
        "username": "",
        "password": "",
        "backup_dir": os.path.join(".", "gc_backup"),
        "export_formats": "fit",
        "ignore_errors": False,
        "max_retries": 3,
        "download_from_date": "1900-01-01 00:00:00"
    }

    config_file = os.path.expanduser(config_file)
    if not os.path.isfile(config_file):
        print("Configuration file not found: " + config_file)
        return

    with open(config_file) as f:
        try:
            user_config = json.load(f)
        except json.decoder.JSONDecodeError as err:
            print("Configuration file error: " + str(err))
            return

    config.update(user_config)

    if not os.path.isdir(config["backup_dir"]):
        os.makedirs(config["backup_dir"])

    rr = Retryer(
        delay_strategy=ExponentialBackoffDelayStrategy(
            initial_delay=timedelta(seconds=1)),
        stop_strategy=MaxRetriesStopStrategy(config["max_retries"]))

    with GarminClient(config["username"], config["password"]) as gc:
        # get all activity ids and timestamps
        print("Scanning activities for {}".format(config["username"]))
        activities = rr.call(gc.list_activities)
        print("Total activities: {}".format(len(
            activities)))
        # print(activities)

        from_date_str = config["download_from_date"]
        new_activities = get_activities_since(activities, from_date_str)
        print("Activities to backup[since: {}]: {}"
              .format(from_date_str, len(new_activities)))

        last_date = None
        for i, activity in enumerate(new_activities):
            _id, activity_date = activity
            print("Downloading[{}]: {} - {}".format(i, _id, activity_date))
            try:
                garminexport.backup.download(gc, activity, rr,
                                             config["backup_dir"],
                                             config["export_formats"])
            except Exception as err:
                print("failed with exception: {}".format(err))
                if not config["ignore_errors"]:
                    raise
            if last_date is None or last_date < activity_date:
                last_date = activity_date

        store_last_activity_date_in_config_file(config_file, config, last_date)


def store_last_activity_date_in_config_file(config_file, config, last_date):
    if last_date:
        print("Storing last activities date: {}".format(last_date))
        config["download_from_date"] = last_date.strftime("%Y-%m-%d %H:%M:%S")
        with open(config_file, 'w') as outfile:
            json.dump(config, outfile, indent=4)


def get_activities_since(activities, from_date):
    answer = []
    try:
        from_date = datetime.strptime(from_date, "%Y-%m-%d %H:%M:%S")
        utczone = tz.gettz('UTC')
        from_date = from_date.replace(tzinfo=utczone)
    except ValueError as err:
        print("Bad date! " + str(err))
        return answer

    while activities:
        a = activities.pop()
        if a[1] > from_date:
            answer.append(a)

    return answer


# Add command line arguments and run
parser = argparse.ArgumentParser(description='Garmin Connect Fit Fetcher')
parser.add_argument('--config', default='~/.config/gcff/config.json', type=str,
                    help='Your configuration file')
args = parser.parse_args()

if __name__ == '__main__':
    if args.config:
        gcff(args.config)
    else:
        parser.print_help()
