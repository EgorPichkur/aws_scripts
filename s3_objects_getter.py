import argparse
import boto3
import sys
import os

from datetime import datetime
from dateutil.tz import tzutc
from pprint import pprint

from helpers.parser import credential_file_parser


def get_credentials(profile_name: str) -> dict:
    credentials = credential_file_parser(os.getenv("AWS_CREDS_FILE_PATH"))

    creds = None
    for record in credentials:
        for profile in record:
            if profile == profile_name:
                creds = record[profile]
                break
        if creds is not None:
            break
    if not creds:
        raise KeyError("Unknown profile name!")
    return creds

def format_time(time_string: str) -> datetime:
    try:
        print(time_string)
        d = datetime.strptime(time_string, "%d-%m-%Y %H:%M:%S")
        d = d.replace(tzinfo=tzutc())
        return d
    except ValueError:
        msg = "The maximum datetime for the requested object in format %d-%m-%Y %H:%M:%S"
        raise argparse.ArgumentTypeError(msg)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("bucket", help="Bucket name")
    parser.add_argument("filename", help="Path to a requested file in the bucket")
    parser.add_argument(
        "-n",
        "--no_newer_than",
        type=format_time,
        help="The maximum datetime for the requested object in format %d-%m-%Y %H:%M:%S",
        default=datetime(2000, 1, 1, tzinfo=tzutc())
    )
    parser.add_argument("-p", "--profile", default="default", help="AWS IAM user credentials profile")
    parser.add_argument("output", help="Path to an output file")
    args = parser.parse_args()
    access_keys = None
    try:
        access_keys = get_credentials(args.profile)
    except OSError as e:
        print(f"Unexpected error has happened! Here it is: {e}")
        sys.exit(1)

    # TODO: add some error handling

    s3 = boto3.client(
        "s3",
        aws_access_key_id=access_keys["aws_access_key_id"],
        aws_secret_access_key=access_keys["aws_secret_access_key"]
    )
    versions = s3.list_object_versions(Bucket=args.bucket, Prefix=args.filename)

    latest_version_id = None
    for version in versions["Versions"]:
        if version["LastModified"] < args.no_newer_than:
            latest_version_id = version["VersionId"]
            print(latest_version_id)
            break
    if not latest_version_id:
        print(f"There is no version of the object {args.filename} newer than {args.no_newer_than}")
        sys.exit(2)
    obj = s3.get_object(Bucket=args.bucket, Key=args.filename, VersionId=latest_version_id)
    f = open(args.output, "wb")
    for chunk in obj["Body"].iter_chunks():
        f.write(chunk)
    f.close()
