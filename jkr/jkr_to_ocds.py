#!/usr/bin/python

from __future__ import print_function
import os
import fnmatch
import json
import uuid
import datetime

def ocds_party(parse):
    # parse data for parties
    jkr_id = "none" # id not found in source
    jkr_name = parse["contractor"]
    # assign data into parties fields
    party_data = {
        "id": jkr_id,
        "name": jkr_name,
        "role": "supplier"
    }
    return party_data

def ocds_award(parse):
    # parse data for award
    jkr_date = parse["advertise_date"] # assume awarded date is same
    jkr_desc = "none" # description is found as title
    jkr_status = "unknown" # status not available readily
    jkr_title = parse["title"]
    cost = parse["cost"]
    if len(cost) == 0:
        jkr_amount = 0 # set 0 if cost has empty string
    else:
        cost = cost.replace(',', '') # remove comma
        cost = cost.replace('RM ', '') # remove currency and space
        jkr_amount = cost
    # assign data into award fields
    award_data = {
        "date": jkr_date,
        "description": jkr_desc,
        "id": uuid.uuid4().hex,
        "status": jkr_status,
        "title": jkr_title,
        "value": {
            "amount": float(jkr_amount),
            "currency": "MYR"
        }
    }
    return award_data

def ocds_release(parse):
    # parse data for each release
    award_list = []
    award = ocds_award(parse)
    award_list.append(award)
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
        "tag": ["compiled"],
        "tender": {}
    }
    return release_data

def ocds_record_releases(parse):
    # parse data for each release in record
    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    tag_list = ["award"] # releases contain only award
    url_data = parse["dataURL"] # no file for releases
    # assign data into record releases fields
    record_releases_data = {
        "date": now,
        "tag": tag_list,
        "url": url_data
    }
    return record_releases_data

def ocds_record(parse):
    # parse data for each record
    release_data = ocds_release(parse)
    ocid = release_data["ocid"]
    release_list = []
    release_list.append(ocds_record_releases(parse))
    # assign data into record fields
    record_data = {
        "compiledRelease": release_data,
        "ocid": ocid,
        "releases": release_list
    }
    return record_data

def ocds_package(parse):
    # parse data for package metadata
    package_list = []
    package_list.append(parse["dataURL"]) # no files for releases
    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    record_list = []
    record_list.append(ocds_record(parse)) # only one record
    uri = parse["fileURL"]
    # assign data into package fields
    package_data = {
        "packages": package_list,
        "publishedDate": now,
        "publisher": {
            "name": "Sinar/ocds-scripts"
        },
        "records": record_list,
        "uri": uri,
        "version": "1.0"
    }
    return package_data

def jkr_to_ocds(path, parse_ls):
    for fname in parse_ls:
        # retrieve JSONL file in JKR format
        fpath = path + '/' + fname
        print('Read from {}'.format(fpath))
        jkr_file = open(fpath, 'r')
        # prepare JSONL file in OCDS format
        ocds_fname = 'ocds-' + fname
        ocds_fpath = path + '/' + ocds_fname
        print('Write to {}'.format(ocds_fpath))
        ocds_file = open(ocds_fpath, 'w')
        # prepare addtional data for use in OCDS format
        ocds_url_home = 'https://github.com/Sinar/ocds-scripts'
        ocds_url_data = ocds_url_home + '/raw/master/jkr/data'
        ocds_url_file = ocds_url_data + '/' + ocds_fname
        # convert each line from JKR to OCDS format
        for line in jkr_file:
            data = json.loads(line)
            # include additional data in JSON...
            data["homeURL"] = ocds_url_home # for publisher/uri
            data["dataURL"] = ocds_url_data # for releases/url
            data["fileURL"] = ocds_url_file # for uri
            # ...and parse JKR and additional data together
            ocds_data = ocds_package(data)
            dump_data = json.dumps(ocds_data)
            ocds_file.write(dump_data + '\n')
        ocds_file.close()
        jkr_file.close()

def main():
    path = './data' # location of files
    blob = 'jkr*.jsonl' # name of files to match
    name_ls = []
    for name in os.listdir(path):
        if fnmatch.fnmatch(name, blob):
            name_ls.append(name)
    name_ls.sort()
    if len(name_ls) == 0:
        print('File not found: {0}/{1}'.format(path, blob))
    else:
        jkr_to_ocds(path, name_ls)
    print('Finish')

if __name__ == '__main__':
    main()
