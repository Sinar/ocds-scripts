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
    entry = parse["Profil"]
    cidb_id = entry["Nombor Pendaftaran"]
    cidb_name = parse["name"]
    party_data = {
        "id": cidb_id,
        "name": cidb_name,
        "role": "supplier"
    }
    return party_data 

def ocds_award(parse):
    entry = parse["projects"][0] # only the first entry in list
    cidb_project = entry["project"]
    cidb_date = entry["dates"]
    cidb_amount = entry["value"].replace(',','') # remove comma
    award_data = {
        "id": uuid.uuid4().hex,
        "description": cidb_project,
        "status": "complete",
        "date": cidb_date,
        "value": {
            "amount": float(cidb_amount),
            "currency": "MYR"
        }
    }
    return award_data

def ocds_award_record(parse):
    party_data = ocds_party(parse)
    if len(parse["projects"]) == 0:
        award_data = "None" # some CIDB entries do not have project
    else:
        award_data = ocds_award(parse)
    ocid = uuid.uuid4().hex
    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    award_record_data = {
        "ocid": ocid,
        "id": ocid + "01-award",
        "date": now,
        "language":"en",
        "tag":[ "contract" ], 
        "initiationType":"Tender",
        "parties": [ party_data ],
        "buyer": {},
        "award":[ award_data ]
    }
    return award_record_data

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
            ocds_data = ocds_award_record(data)
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
