import csv
import os
import json
import sys

from dataclasses import dataclass
from urllib.parse import urlsplit
import tldextract as tld

@dataclass
class DomainInfo:
    domain: str
    count: int

@dataclass
class PostData:
    key: str
    data: str

def main():
    argv = sys.argv
    interested_domains: list[str] = []
    while "-f" in argv:
        i = argv.index("-f")
        argv.remove("-f")

        if i >= len(argv):
            print("Invalid use of '-f'!")
            return
        
        domain = argv[i]
        argv.remove(domain)
        interested_domains.append(domain)

    filename = ""

    if len(argv) <= 1:
        print("No path supplied, searching current dir...")
        for file in os.listdir():
            if file.endswith(".har"):
                print(f"Found \"{file}\"!")
                filename = file
                break
            if filename == "":
                print("No suitable file found! Exiting...")
                return
    else:
        filename = argv[1]

    print(f"Parsing file \"{filename}\"")

    # parse file
    har_text = ""
    with open(filename, 'r') as file:
        har_text = file.read()
        print(f"Read {len(har_text)} characters from \"{filename}\".\n")
    
    if har_text.isspace():
        return

    urls: dict[str, DomainInfo] = {}
    post_data: list[PostData] = []
    try:
        har_json = json.loads(har_text)
        har_log = har_json["log"]

        _pages = har_log["pages"]

        entries = har_log["entries"]

        for entry in entries:
            request = entry["request"]
            url = str(request["url"])
            split_url = urlsplit(url)
            
            key = split_url.scheme + "://" + split_url.netloc
            if key in urls.keys():
                urls[key].count += 1
            else:
                domain = tld.extract(url).top_domain_under_public_suffix
                urls[key] = DomainInfo(domain, 1)

            if "postData" in request.keys():
                post_data_str = request["postData"]
                post_data.append(PostData(key, json.dumps(post_data_str)))

    except Exception as e:
        print(f"Failed to parse file! Error:\n{e}")
        return

    savefile = "data.csv"
    if "-c" in argv:
        i = argv.index("-c")
        argv.remove("-c")

        if i >= len(argv):
            print("Invalid use of '-c'!")
            return
        
        savefile = argv[i]
        argv.remove(savefile)

    urls = dict(sorted(urls.items()))
    with open(savefile, "w", newline="") as csvfile:
        writer = csv.writer(csvfile, delimiter=",", quotechar="|", quoting=csv.QUOTE_MINIMAL)
        for url, domainInfo in urls.items():
            writer.writerow([url, domainInfo.count, "", domainInfo.domain])

    print(f"Written parsed data to \"{savefile}\"")

    savefile = "data.txt"
    if "-o" in argv:
        i = argv.index("-o")
        argv.remove("-o")

        if i >= len(argv):
            print("Invalid use of '-o'!")
            return
        
        savefile = argv[i]
        argv.remove(savefile)

    with open(savefile, "w", newline="") as file:
        for data in post_data:
            _ = file.write(f"\n{'-'*30}\n{data.key}:\n{data.data}\n")

    print(f"Written parsed data to \"{savefile}\"")

if __name__ == "__main__":
    main()
