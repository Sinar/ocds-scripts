#!/usr/bin/python

from __future__ import print_function
import os
import fnmatch
import json
import uuid
import datetime

def list_jsonl(spath, blob):
    name_ls = []
    for name in os.listdir(spath):
        if fnmatch.fnmatch(name, blob):
            name_ls.append(name)
    name_ls.sort()
    return name_ls

def ocds_party(parse):
    cidb_id = parse["Profil"]["Nombor Pendaftaran"]
    cidb_name = parse["name"]
    party_data = {
        "id": cidb_id,
        "name": cidb_name,
        "role": "supplier"
    }
    return party_data 

def ocds_award(parse):
    cidb_project = parse["project"]
    cidb_date = parse["dates"]
    cidb_amount = parse["value"].replace(',','') # remove comma
    award_data = {
        "date": cidb_date,
        "description": "None",
        "id": uuid.uuid4().hex,
        "status": "complete",
        "title": cidb_project,
        "value": {
            "amount": float(cidb_amount),
            "currency": "MYR"
        }
    }
    return award_data

def ocds_release(parse):
    # parse data for each release
    award_list = []
    projects = parse["projects"]
    if len(projects) >= 2:
        for project in projects:
            award = ocds_award(project)
            award_list.append(award)
    elif len(projects) == 1:
        award_list.append(ocds_award(projects[0])) # only one project
    else:
        award_list.append("None")
    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    ocid = uuid.uuid4().hex
    party_list = []
    party_list.append(ocds_party(parse))
    # assign data into release fields
    release_data = {
        "award": award_list,
        "buyer": {},
        "date": now,
        "id": ocid + "01-award",
        "initiationType": "tender",
        "language": "en",
        "ocid": ocid,
        "parties": party_list,
        "tag": [ "contract" ],
        "tender": {}
    }
    return release_data

def ocds_package(parse):
    # parse data for package metadata
    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    release_list = []
    release_list.append(ocds_release(parse))
    # assign data into package fields
    package_data = {
        "version": "1.0",
        "publishedDate": now,
        "publisher": {
            "name": "Sinar/ocds-scripts"
        },
        "uri": "https://github.com/Sinar/ocds-scripts",
        "releases": release_list
    }
    return package_data

def cidb_to_ocds(path, parse_ls):
    for each_file in parse_ls:
        # retrieve JSONL file in CIDB format
        fname = each_file # <type 'str'>
        fpath = path + '/' + each_file
        print('Read from {}'.format(fpath))
        cidb_file = open(fpath, 'r')
        # prepare JSONL file in OCDS format
        ocds_fname = 'ocds-' + fname
        ocds_fpath = path + '/' + ocds_fname
        print('Write to {}'.format(ocds_fpath))
        ocds_file = open(ocds_fpath, 'w')
        for each_obj in cidb_file:
            data = json.loads(each_obj)
            ocds_data = ocds_package(data)
            dump_data = json.dumps(ocds_data)
            ocds_file.write(dump_data + '\n')
        ocds_file.close()
        cidb_file.close()

def main():
    path = './data' # location of files
    blob = 'contractors*.jsonl' # name of files to match
    parse_ls = list_jsonl(path, blob)
    cidb_to_ocds(path, parse_ls)
    print('Finish')

if __name__ == '__main__':
    main()
