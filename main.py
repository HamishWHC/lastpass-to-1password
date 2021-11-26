import csv
import datetime
import json
import os
from pprint import pprint
from typing import Dict, List

note_types_to_categories = {
    "Database": "database",
    "Server": "server",
}


def login_transform(to_create, item):
    to_create["fields"][0]["value"] = item["username"]
    to_create["fields"][1]["value"] = item["password"]

    to_create["notesPlain"] = item["notes"]
    return to_create


def secure_note_transform(to_create, item):
    to_create["notesPlain"] = item["notes"]
    return to_create


def database_transform(to_create, item):
    to_create["sections"][0]["fields"][0]["v"] = item["fields"]["type"]
    to_create["sections"][0]["fields"][1]["v"] = item["fields"]["hostname"]
    to_create["sections"][0]["fields"][2]["v"] = item["fields"]["port"]
    to_create["sections"][0]["fields"][3]["v"] = item["fields"]["database"]
    to_create["sections"][0]["fields"][4]["v"] = item["fields"]["username"]
    to_create["sections"][0]["fields"][5]["v"] = item["fields"]["password"]
    to_create["sections"][0]["fields"][6]["v"] = item["fields"]["sid"]
    to_create["sections"][0]["fields"][7]["v"] = item["fields"]["alias"]

    to_create["notesPlain"] = item["fields"]["notes"]
    return to_create


def server_transform(to_create, item):
    to_create["sections"][0]["fields"][0]["v"] = item["fields"]["hostname"]
    to_create["sections"][0]["fields"][1]["v"] = item["fields"]["username"]
    to_create["sections"][0]["fields"][2]["v"] = item["fields"]["password"]

    to_create["notesPlain"] = item["fields"]["notes"]
    return to_create


category_to_transform = {
    "login": login_transform,
    "securenote": secure_note_transform,
    "database": database_transform,
    "server": server_transform
}


def tag_transform(grouping: str):
    return grouping.replace("\\", "#####").replace("/", " & ").replace("#####", "/")


def parse_note(item: Dict[str, str]):
    if item["extra"].startswith("NoteType:"):
        lines = item["extra"].split("\n")

        note_type = lines[0].split(":", 1)[1]
        if note_type not in note_types_to_categories:
            return None

        fields = {}
        for i, line in enumerate(lines[1:], start=1):
            line = line.strip()
            if line == "":
                continue
            parts = line.split(":", 1)
            if parts[0] == "Notes":
                fields["notes"] = "\n".join([parts[1], *lines[i+1:]])
            fields[parts[0].lower()] = parts[1]

        return {
            "category": note_types_to_categories[note_type],
            "title": item["name"],
            "fields": fields,
            "tag": tag_transform(item["grouping"]),
            "is_favourite": item["fav"] == "1"
        }
    else:
        return {
            "category": "securenote",
            "title": item["name"],
            "notes": item["extra"],
            "tag": tag_transform(item["grouping"]),
            "is_favourite": item["fav"] == "1"
        }


def read_lastpass_export(filename: str) -> List[Dict[str, str]]:
    with open(filename, "r") as f:
        reader = csv.DictReader(f)

        items = []
        for item in reader:
            if item["url"] != "http://sn":
                items.append({
                    "category": "login",
                    "title": item["name"],
                    "website": item["url"],
                    "username": item["username"],
                    "password": item["password"],
                    "notes": item["extra"],
                    "tag": tag_transform(item["grouping"]),
                    "is_favourite": item["fav"] == "1"
                })
            else:
                note = parse_note(item)
                if note is not None:
                    items.append(note)

    return items


def read_bash_return(cmd, single=True):
    process = os.popen(cmd)
    preprocessed = process.read()
    process.close()
    if single:
        return str(preprocessed.split("\n")[0])
    else:
        return str(preprocessed)


def import_into_1password(items: List[Dict[str, str]]):
    import_tag = f'"LastPass Import {datetime.datetime.now().isoformat()}"'

    retrieved_templates = set()
    for item in items:
        if item["category"] not in category_to_transform:
            continue

        if item["category"] not in retrieved_templates:
            template = read_bash_return(
                f"op get template {item['category']}")
            with open(f"templates/{item['category']}.json", "w") as f:
                f.write(template)
            retrieved_templates.add(item["category"])

        with open(f"templates/{item['category']}.json", "r") as f:
            item_to_create = json.load(f)

        item_to_create = category_to_transform[item["category"]](
            item_to_create, item)

        with open(f"tmp.json", "w") as f:
            json.dump(item_to_create, f)

        print(f"Creating {item['title']}...")

        tags = ','.join([import_tag, f'"{item["tag"]}"'])
        cmd = f"op create item {item['category']} --template tmp.json --title \"{item['title']}\" --tags {tags}"
        if item["category"] == "login":
            cmd += f" --url {item['website']}"
        read_bash_return(cmd)


items = read_lastpass_export("lastpass_export.csv")

try:
    import_into_1password(items)
except KeyboardInterrupt:
    os.remove("tmp.json")
