from typing import List, Dict

def credential_file_parser(credentials_file_path: str) -> List[Dict[str, Dict[str, str]]]:
    try:
        credentials = []
        profile_name = None
        profile_keys = {}
        with open(credentials_file_path, "r", encoding="utf-8") as creds_file:
            for line in creds_file:
                if line.startswith("["):
                    if profile_name is not None and profile_name != line.strip("[]"):
                        credentials.append({profile_name: profile_keys})
                        profile_keys = {}
                    profile_name = line.strip("[]\n")
                else:
                    key_id, key_value = line.split("=")
                    key_id = key_id.strip(" ")
                    key_value = key_value.strip(" \n")
                    profile_keys[key_id] = key_value
    except OSError as file_opening_error:
        print(f"Something went wrong!\n{file_opening_error}")
        raise OSError from None

    return credentials

