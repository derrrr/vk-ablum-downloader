import re
import os
import time
import requests


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
                      "(khtml, like gecko) "
                      "chrome/46.0.2490.86 safari/537.36"}
    session.headers.update(headers)
    return session


def grab_img(url, output_folder):
    rs = _get_session()
    res = rs.get(url).text.replace("\\/", "/").replace("\\\"", "\"")
    img_src = re.findall("z_src\":\"([\w:/\.]+/([\w\.]+))\"", res)

    for img_url, name in img_src:
        output_img = "{}/{}".format(output_folder, name)

        if not os.path.exists(output_img):
            with open(output_img, "wb") as handle:
                response = rs.get(img_url, stream=True)
                if not response.ok:
                    print(response)

                for block in response.iter_content(1024):
                    if not block:
                        break

                    handle.write(block)
            print("saved as {}".format(name))


def get_link_list():
    with open(link_text) as f:
        content = f.readlines()
        return [x.strip() for x in content]


link_text = "R:/link.txt"
output_folder = "R:/folder"


@timeit
def process():
    link_list = get_link_list()

    if not os.path.exists(output_folder):
        os.makedirs(output_folder, mode=0o777)
    for link in link_list:
        grab_img(link, output_folder)


process()
