#!/usr/bin/python

from __future__ import print_function
import os
import fnmatch
import json
import uuid
import datetime

def ocds_party(parse):
    # parse data for parties
    cidb_id = parse["Profil"]["Nombor Pendaftaran"]
    cidb_name = parse["name"]
    # assign data into parties fields
    party_data = {
        "id": cidb_id,
        "name": cidb_name,
        "role": "supplier"
    }
    return party_data

def ocds_award(parse):
    # parse data for award
    cidb_date = parse["dates"]
    cidb_title = parse["project"]
    cidb_amount = parse["value"].replace(',', '') # remove comma
    # assign data into award fields
    award_data = {
        "date": cidb_date,
        "description": "none",
        "id": uuid.uuid4().hex,
        "status": "complete",
        "title": cidb_title,
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
    if len(projects) >= 1:
        for project in projects:
            award = ocds_award(project)
            award_list.append(award)
    else:
        award_list.append("none")
    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    ocid = uuid.uuid4().hex
    party_list = []
    party_list.append(ocds_party(parse))
    # assign data into release fields
    release_data = {
        "award": award_list,
        "buyer": {}, #FIXME: buyer:name is missing but required
        "date": now,
        "id": ocid + "01-award",
        "initiationType": "tender",
        "language": "en",
        "ocid": ocid,
        "parties": party_list,
        "tag": ["compiled"],
        "tender": {} #FIXME: tender:id is missing but required
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

def cidb_to_ocds(path, parse_ls):
    for fname in parse_ls:
        # retrieve JSONL file in CIDB format
        fpath = path + '/' + fname
        print('Read from {}'.format(fpath))
        cidb_file = open(fpath, 'r')
        # prepare JSONL file in OCDS format
        ocds_fname = 'ocds-' + fname
        ocds_fpath = path + '/' + ocds_fname
        print('Write to {}'.format(ocds_fpath))
        ocds_file = open(ocds_fpath, 'w')
        # prepare addtional data for use in OCDS format
        ocds_url_home = 'https://github.com/Sinar/ocds-scripts'
        ocds_url_data = ocds_url_home + '/raw/master/cidb/data'
        ocds_url_file = ocds_url_data + '/' + ocds_fname
        # convert each line from CIDB to OCDS format
        for line in cidb_file:
            data = json.loads(line)
            # include additional data in JSON...
            data["homeURL"] = ocds_url_home # for publisher/uri
            data["dataURL"] = ocds_url_data # for releases/url
            data["fileURL"] = ocds_url_file # for uri
            # ...and parse CIDB and additional data together
            ocds_data = ocds_package(data)
            dump_data = json.dumps(ocds_data)
            ocds_file.write(dump_data + '\n')
        ocds_file.close()
        cidb_file.close()

def main():
    path = './data' # location of files
    blob = 'contractors*.jsonl' # name of files to match
    name_ls = []
    for name in os.listdir(path):
        if fnmatch.fnmatch(name, blob):
            name_ls.append(name)
    name_ls.sort()
    if len(name_ls) == 0:
        print('File not found: {0}/{1}'.format(path, blob))
    else:
        cidb_to_ocds(path, name_ls)
    print('Finish')

if __name__ == '__main__':
    main()
