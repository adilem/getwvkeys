"""
 This file is part of the GetWVKeys project (https://github.com/GetWVKeys/getwvkeys)
 Copyright (C) 2022 Notaghost, Puyodead1 and GetWVKeys contributors 
 
 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU Affero General Public License as published
 by the Free Software Foundation, version 3 of the License.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Affero General Public License for more details.

 You should have received a copy of the GNU Affero General Public License
 along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import argparse
import base64
import json
import sys

import requests

# Version of the API the script is for. This should be changed when the API is updated.
API_VERSION = "5"
# Version of the individual script
SCRIPT_VERSION = "5.1"
# Dynamic injection of the API url
API_URL = "__getwvkeys_api_url__"

# Change your headers here
def headers():
    return {"Connection": "keep-alive", "accept": "*/*"}


# CHANGE THIS FUNCTION TO PARSE LICENSE URL RESPONSE
def post_request(args, challenge):
    r = requests.post(args.url, headers=args.headers, data=challenge, timeout=10)
    if not r.ok:
        print("[-] Failed to get license: [{}] {}".format(r.status_code, r.text))
        exit(1)
    if args.verbose:
        # printing the raw license data can break terminals
        print("[+] License response:\n", base64.b64encode(r.content).decode("utf-8"))
    return r.content


# Do Not Change Anything in this class
class GetWVKeysApi:
    def __init__(self, args) -> None:
        # dynamic injection of the API url
        self.baseurl = "https://getwvkeys.cc" if API_URL == "__getwvkeys_api_url__" else API_URL
        self.api_url = self.baseurl + "/pywidevine"
        self.args = args
        self.args.headers = headers()

    def generate_request(self):
        if self.args.verbose:
            print("[+] Generating License Request ")
        data = {"pssh": self.args.pssh, "buildInfo": self.args.buildinfo, "force": self.args.force, "license_url": self.args.url}
        header = {"X-API-Key": args.auth, "Content-Type": "application/json"}
        r = requests.post(self.api_url, json=data, headers=header)
        if not r.ok:
            if "error" in r.text:
                # parse the response as a json error
                error = json.loads(r.text)
                print("[-] Failed to generate license request: [{}] {}".format(error.get("code"), error.get("message")))
                exit(1)
            print("[-] Failed to generate license request: [{}] {}".format(r.status_code, r.text))
            exit(1)

        data = r.json()

        if "X-Cache" in r.headers:
            keys = data["keys"]
            print("\n" * 5)
            print("[+] Keys (from cache):")
            for k in keys:
                print("--key {}".format(k["key"]))
            exit(0)

        self.session_id = data["session_id"]
        challenge = data["challenge"]

        if self.args.verbose:
            print("[+] License Request Generated\n", challenge)
            print("[+] Session ID:", self.session_id)

        return base64.b64decode(challenge)

    def decrypter(self, license_response):
        if self.args.verbose:
            print("[+] Decrypting with License Request and Response ")
        data = {
            "pssh": self.args.pssh,
            "response": license_response,
            "license_url": self.args.url,
            "headers": self.args.headers,
            "buildInfo": self.args.buildinfo,
            "force": self.args.force,
            "session_id": self.session_id,
        }
        header = {"X-API-Key": args.auth, "Content-Type": "application/json"}
        r = requests.post(self.api_url, json=data, headers=header)
        if not r.ok:
            if "error" in r.text:
                # parse the response as a json error
                error = json.loads(r.text)
                print("[-] Failed to decrypt license: [{}] {}".format(error.get("code"), error.get("message")))
                exit(1)
            print("[-] Failed to decrypt license: [{}] {}".format(r.status_code, r.text))
            exit(1)
        return r.json()

    def main(self):
        license_request = self.generate_request()
        if args.verbose:
            print("[+] Sending License URL Request")
        license_response = post_request(args, license_request)
        decrypt_response = self.decrypter(base64.b64encode(license_response).decode())
        keys = decrypt_response["keys"]
        session_id = decrypt_response["session_id"]

        if args.verbose:
            print(json.dumps(decrypt_response, indent=4))
            print("Decryption Session ID:", session_id)
        print("\n" * 5)
        print("[+] Keys:")
        for k in keys:
            print("--key {}".format(k))


if __name__ == "__main__":
    getwvkeys_api_key = "__getwvkeys_api_key__"
    banner = """
   ____      _ __        ____     ___  __              
  / ___| ___| |\\ \\      / /\\ \\   / / |/ /___ _   _ ___ 
 | |  _ / _ \\ __\\ \\ /\\ / /  \\ \\ / /| ' // _ \\ | | / __|
 | |_| |  __/ |_ \\ V  V /    \\ V / | . \\  __/ |_| \\__ \\
  \\____|\\___|\\__| \\_/\\_/      \\_/  |_|\\_\\___|\\__, |___/
                                             |___/     
                    Script Version: {}
                    API Version: {}
    """.format(
        SCRIPT_VERSION, API_VERSION
    )
    print(banner)

    parser = argparse.ArgumentParser()
    parser.add_argument("-url", help="License URL")
    parser.add_argument("-pssh", help="PSSH")
    parser.add_argument("-auth", "-api_key", help="GetWVKeys API Key")  # auth is deprecated, use api_key instead. auth will be removed in the next major version
    parser.add_argument("--verbose", "-v", help="increase output verbosity", action="store_true")
    parser.add_argument("--force", "-f", help="Force fetch, bypasses cache (You should only use this if the cached keys are not working). Default is OFF", default=False, action="store_true")
    parser.add_argument("--buildinfo", "-b", default="", help="Buildinfo", required=False)
    parser.add_argument("--version", "-V", help="Print version and exit", action="store_true")

    args = parser.parse_args()
    args.auth = getwvkeys_api_key if getwvkeys_api_key != "__getwvkeys_api_key__" else args.auth

    if args.version:
        print(f"GetWVKeys Generic v{SCRIPT_VERSION} for API Version {API_VERSION}")
        exit(0)

    while (args.url is None or args.pssh is None) or (args.url == "" or args.pssh == ""):
        if not args.url:
            args.url = input("Enter License URL: ")
        if not args.pssh:
            args.pssh = input("Enter PSSH: ")
        if not args.auth:
            args.auth = input("Enter GetWVKeys API Key: ")

    if len(sys.argv) == 1:
        parser.print_help()
        print()
        args.buildinfo = ""
        args.verbose = False

    try:
        start = GetWVKeysApi(args)
        start.main()
    except Exception as e:
        raise
