#!/usr/bin/env python

import os
import sys
import argparse
import requests
import json
import string
import random

from bs4 import BeautifulSoup

TOKEN_URL = "https://www.diawi.com/"
UPLOAD_URL = 'https://upload.diawi.com/plupload.php'
POST_URL = 'https://upload.diawi.com/plupload'
STATUS_URL = 'https://upload.diawi.com/status'


def validate_file(args):
    if not os.path.isfile(args.file):
        print("File does not exist!")
        sys.exit(1)

    name, extention = os.path.splitext(args.file)

    if extention == ".ipa" or extention == ".zip" or extention == ".apk":
        return True
    else:
        print("File type not accepted!")
        sys.exit(1)


def create_tmp_file_name(args):
    name, extention = os.path.splitext(args.file)

    return "o_{}{}".format(''.join(random.SystemRandom().choice(
        string.ascii_lowercase + string.digits) for _ in range(29)), extention)


def get_token():
    r = requests.get(TOKEN_URL)

    if r.status_code == 200:
        soup = BeautifulSoup(r.text, 'html.parser')
        token = soup.find("input", type="hidden")["value"]

        if token is None:
            print("Could not get token!")
            sys.exit(1)
        else:
            print("found token : {}".format(token))
            return token
    else:
        print("{} not available!".format(TOKEN_URL))


def file_upload(args, tmp_file_name, token):
    files = {'file': open(args.file, 'rb')}
    upload_data = {'name': tmp_file_name}
    upload_params = {'token': token}

    print("Uploading File...")
    r = requests.post(UPLOAD_URL, params=upload_params, files=files, data=upload_data)

    if r.status_code != 200:
        print("Failed to upload file!")
        sys.exit(1)

    print("Upload complete!")


def file_post(args, tmp_file_name, token):
    file_name = os.path.basename(args.file)

    post_data = {
        'token': token,
        'uploader_0_tmpname': tmp_file_name,
        'uploader_0_name': file_name,
        'uploader_0_status': 'done',
        'uploader_count': '1',
        'comment': args.comment if args.comment else '',
        'email': args.email if args.email else '',
        'password': args.password if args.password else '',
        'notifs': 'on' if args.notif else 'off',
        'udid': 'on' if args.udid else 'off',
        'wall': 'on' if args.wall else 'off'
    }

    print("Posting File...")
    r = requests.post(POST_URL, data=post_data)

    if r.status_code != 200:
        print("Failed to post file!")
        sys.exit(1)

    json_result = json.loads(r.text)
    print(json_result["job"])
    return json_result["job"]


def get_job_status(job_id):
    print("Getting status...")

    status_params = {'job': job_id}
    r = requests.get(STATUS_URL, params=status_params)

    json_result = json.loads(r.text)
    if json_result["message"] == "Ok":
        print("Your app can be downloaded at : {}".format(json_result["link"]))
    else:
        print("Your app failed to post")
        sys.exit(1)


def main(args):
    validate_file(args)
    tmp_file_name = create_tmp_file_name(args)
    token = get_token()
    file_upload(args, tmp_file_name, token)
    job_id = file_post(args, tmp_file_name, token)
    get_job_status(job_id)

    print("Finished!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("file",             help="Path to your deploy file (.ipa .zip .apk)")
    parser.add_argument("-c", "--comment",  help="Comment to display to the installer")
    parser.add_argument("-e", "--email",    help="Email to receive the deployed app link")
    parser.add_argument("-p", "--password", help="Password for the deployed app")
    parser.add_argument("-n", "--notif",    help="Notify when user installs application", action="store_true")
    parser.add_argument("-u", "--udid",     help="Allow testers to find by UDID on Daiwi", action="store_true")
    parser.add_argument("-w", "--wall",     help="List icon on Diawi 'Wall of Apps'", action="store_true")
    args = parser.parse_args()

    main(args)
