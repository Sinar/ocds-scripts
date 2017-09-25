#!/usr/bin/python

from __future__ import print_function
import os
import fnmatch
import json
import uuid
import datetime

def ocds_party(parse):
    # parse data for parties
    myproc_id = parse["tender_number"]
    myproc_name = parse["successful_tenderer"] # bad string
    # assign data into parties fields
    party_data = {
        "id": myproc_id,
        "name": myproc_name,
        "role": "supplier"
    }
    return party_data

def ocds_award(parse):
    # parse data for award
    myproc_date = "none" # date field not found in source
    myproc_desc = "none" # description is found as title
    myproc_status = "unknown" # status cannot be determined
    myproc_title = parse["title"]
    cost = parse["agreed_price"]
    cost = cost.replace(',', '') # remove comma
    cost = cost.replace('RM', '') # remove currency
    myproc_amount = cost
    # assign data into award fields
    award_data = {
        "date": myproc_date,
        "description": myproc_desc,
        "id": uuid.uuid4().hex,
        "status": myproc_status,
        "title": myproc_title,
        "value": {
            "amount": float(myproc_amount),
            "currency": "MYR"
        }
    }
    return award_data

def ocds_release(parse):
    # parse data for each release
    award_list = []
    award = ocds_award(parse)
    award_list.append(award)
    buyer_name = parse["ministry"] # omit "agency" field in source
    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    ocid = uuid.uuid4().hex
    party_list = []
    party_list.append(ocds_party(parse))
    # assign data into release fields
    release_data = {
        "award": award_list,
        "buyer": {
            "name": buyer_name
        },
        "date": now,
        "id": ocid + "01-award",
        "initiationType": "tender",
        "language": "en",
        "ocid": ocid,
        "parties": party_list,
        "tag": ["compiled"],
        "tender": {} # FIXME: 'tender:id' is missing but required
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

def myproc_to_ocds(path, parse_ls):
    for fname in parse_ls:
        # retrieve JSONL file in MyProcurement format
        fpath = path + '/' + fname
        print('Read from {}'.format(fpath))
        myproc_file = open(fpath, 'r')
        # prepare JSONL file in OCDS format
        ocds_fname = 'ocds-' + fname
        ocds_fpath = path + '/' + ocds_fname
        print('Write to {}'.format(ocds_fpath))
        ocds_file = open(ocds_fpath, 'w')
        # prepare addtional data for use in OCDS format
        ocds_url_home = 'https://github.com/Sinar/ocds-scripts'
        ocds_url_data = ocds_url_home + '/raw/master/myproc/data'
        ocds_url_file = ocds_url_data + '/' + ocds_fname
        # convert each line from MyProcurement to OCDS format
        for line in myproc_file:
            data = json.loads(line)
            # include additional data in JSON...
            data["homeURL"] = ocds_url_home # for publisher/uri
            data["dataURL"] = ocds_url_data # for releases/url
            data["fileURL"] = ocds_url_file # for uri
            # ...and parse MyProcurement and additional data together
            ocds_data = ocds_package(data)
            dump_data = json.dumps(ocds_data)
            ocds_file.write(dump_data + '\n')
        ocds_file.close()
        myproc_file.close()

def main():
    path = './data' # location of files
    blob = 'keputusan_tender*.jsonl' # name of files to match
    name_ls = []
    for name in os.listdir(path):
        if fnmatch.fnmatch(name, blob):
            name_ls.append(name)
    name_ls.sort()
    if len(name_ls) == 0:
        print('File not found: {0}/{1}'.format(path, blob))
    else:
        myproc_to_ocds(path, name_ls)
    print('Finish')

if __name__ == '__main__':
    main()
