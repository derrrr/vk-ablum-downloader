import re
import os
import time
import json
import requests
import collections


def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        print("{}: {:2.2f} sec".format(method.__name__, te - ts))
        return result
    return timed


def _get_session():
    session = requests.session()
    headers = {
        "user-agent": "mozilla/5.0 (x11; linux x86_64) applewebkit/537.36"
                      "(khtml, like gecko)"
                      "chrome/46.0.2490.86 safari/537.36"
    }
    session.headers.update(headers)
    return session


def get_link_list():
    # Read text line by line
    with open(link_text) as f:
        content = f.readlines()
        return [x.strip() for x in content]


@timeit
def process():
    link_list = get_link_list()
    total_link = len(link_list)
    rs = _get_session()

    if not os.path.exists(output_folder):
        os.makedirs(output_folder, mode=0o777)

    save = 0
    skip = 0
    for link in link_list:
        res = rs.get(link).text.replace("\\/", "/").replace("\\\"", "\"")

        # Set photo_id from photo url
        photo_id = link.split("photo")[1]

        # Set regex pattern for photo info
        pat_id = "".join(["({\"id\":\"", photo_id, ".+]},{\"id\":)"])
        pat_non_id = "".join([",{\"id\":\"(?!", photo_id, ")"])

        # Process photo info to json format
        part_id = re.search(pat_id, res)[0]
        part_id_select = re.split(pat_non_id, part_id)[0]
        part_js = re.sub("\"comments.+>\",", "", part_id_select)

        # Get the higher resolution url from json
        dic_js = json.loads(part_js)
        od = collections.OrderedDict(sorted(dic_js.items()))
        js = [[key, value] for key, value in od.items()]
        img_url = js[-1][1]

        filetype = re.search(".+\.(\w+)", img_url)[1]
        output_img = "{}/photo{}.{}".format(output_folder, photo_id, filetype)

        # Save image
        if not os.path.exists(output_img):
            with open(output_img, "wb") as handle:
                response = rs.get(img_url, stream=True)
                if not response.ok:
                    print(response)
                for block in response.iter_content(1024):
                    if not block:
                        break
                    handle.write(block)
            save += 1
            print("saved as {}. {}/{} done.".format(photo_id[1:], save + skip, total_link))
        else:
            skip += 1
            print("{} exists and skipped. {}/{} done.".format(photo_id[1:], save + skip, total_link))
    return total_link, save, skip


# Set path
link_text = "R:/link.txt"
output_folder = "R:/vk"

total_link, save, skip = process()
print("{} photos: {} saved, {} skipped.".format(total_link, save, skip))
