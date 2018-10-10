#!/usr/bin/env python

import os
import sys
import time
import argparse
import requests           # pip install requests
import json
import string
import random
import re

from bs4 import BeautifulSoup

TOKEN_URL = "https://www.diawi.com/"
UPLOAD_URL = 'https://upload.diawi.com/plupload.php'
POST_URL = 'https://upload.diawi.com/plupload'
STATUS_URL = 'https://upload.diawi.com/status'

set_debug = False


def debug(message):
    if set_debug is True:
        print("debug : {}".format(message))


def log(message):
    print("log : {}".format(message))


def validate_file(args):
    if not os.path.isfile(args.file):
        log("File does not exist!")
        sys.exit(1)
    debug("found file {}".format(args.file))

    name, extention = os.path.splitext(args.file)

    if extention == ".ipa" or extention == ".zip" or extention == ".apk":
        debug("valid file extention : {}".format(extention))
        return True
    else:
        log("File type not accepted!")
        sys.exit(1)


def create_tmp_file_name(args):
    name, extention = os.path.splitext(args.file)

    tmp_file_name = "o_{}{}".format(''.join(random.SystemRandom().choice(
        string.ascii_lowercase + string.digits) for _ in range(29)), extention)

    debug("temp file name : {}".format(tmp_file_name))

    return tmp_file_name


def get_token():
    r = requests.get(TOKEN_URL)

    if r.status_code == 200:
        soup = BeautifulSoup(r.text, 'html.parser')
        #token = soup.find("input", type="hidden")["value"]
        atext = soup.find("script", id="home-js").get_text()
        aline = [line for line in atext.split('\n') if "DIAWI_UPLOAD_TOKEN" in line]
        token = re.findall(r"'(.*?)'", aline[0])

        if token is None:
            log("Could not get token!")
            sys.exit(1)
        else:
            log("found token : {}".format(token))
            return token
    else:
        log("{} not available!".format(TOKEN_URL))


def file_upload(args, tmp_file_name, token):
    files = {'file': open(args.file, 'rb')}
    upload_data = {'name': tmp_file_name}
    upload_params = {'token': token}

    log("Uploading File...")
    r = requests.post(UPLOAD_URL, params=upload_params, files=files, data=upload_data)


    debug("file upload responce code : {}".format(r.status_code))
    debug("file upload responce text : {}".format(r.text))

    if r.status_code != 200:
        log("Failed to upload file!")
        sys.exit(1)

    log("Upload complete!")


def file_post(args, tmp_file_name, token):
    file_name = os.path.basename(args.file)

    post_data = {
        'token': token,
        'uploader_0_tmpname': tmp_file_name,
        'uploader_0_name': file_name,
        'uploader_0_status': 'done',
        'uploader_count': '1',
        'comment': '',
        'email': '',
        'password': '',
        'notifs': 'off',
        'udid': 'off',
        'wall': 'off'
    }

    log("Posting File...")
    r = requests.post(POST_URL, data=post_data)

    debug("file post responce code : {}".format(r.status_code))
    debug("file post responce text : {}".format(r.text))

    if r.status_code != 200:
        log("Failed to post file!")
        sys.exit(1)

    json_result = json.loads(r.text)
    log(json_result["job"])
    return json_result["job"]


def get_job_status(token_id, job_id):
    log("Getting status...")

    status_params = {'token': token_id, 'job': job_id}
    while True:
        r = requests.get(STATUS_URL, params=status_params)

        debug("job status responce code : {}".format(r.status_code))
        debug("job status responce text : {}".format(r.text))

        if r.status_code == 200:
            json_result = json.loads(r.text)
            if json_result["status"] == 2000:
                log("Your app can be downloaded at : {}".format(json_result["link"]))
                break
            else:
                debug("App is not ready, waiting before retry")
                time.sleep(6)
        else:
            log("Server encounted an error")
            sys.exit(1)


def main(args):
    global set_debug

    if args.debug is True:
        set_debug = True

    validate_file(args)
    tmp_file_name = create_tmp_file_name(args)
    token = get_token()
    file_upload(args, tmp_file_name, token)
    job_id = file_post(args, tmp_file_name, token)
    get_job_status(token, job_id)

    log("Finished!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("file",             help="Path to your deploy file (.ipa .zip .apk)")
    parser.add_argument("-c", "--comment",  help="Comment to display to the installer")
    parser.add_argument("-e", "--email",    help="Email to receive the deployed app link")
    parser.add_argument("-p", "--password", help="Password for the deployed app")
    parser.add_argument("-n", "--notif",    help="Notify when user installs application", action="store_true")
    parser.add_argument("-u", "--udid",     help="Allow testers to find by UDID on Daiwi", action="store_true")
    parser.add_argument("-w", "--wall",     help="List icon on Diawi 'Wall of Apps'", action="store_true")
    parser.add_argument("-d", "--debug",    help="Set to enable debug", action="store_true")
    args = parser.parse_args()

    main(args)
