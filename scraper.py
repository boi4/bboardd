#!/usr/bin/env python3
import re
import sys
import os
import shutil
import urllib

from urllib.parse import urlparse
from auth import Auth


def download_bb_page(session, headers, course_id, content_id):
    url = "https://www.ole.bris.ac.uk/webapps/blackboard/content/listContent.jsp"
    values = {
        "course_id": course_id,
        "content_id": content_id,
        "mode": "reset",
    }
    r = session.get(url + "?" + "&".join(k + "=" + values[k] for k in values),
            data=values,
            headers=headers)
    i1 = r.text.find("id=\"pageTitleDiv\"")
    i2 = r.text.find("<!-- Begin bottom list action bar. -->")
    if i1 * i2 == 1:
        print("problems getting full course page", file=sys.stderr)
        return

    return r.text[i1:i2]


def find_h2s(text):
    h2_pos = []
    i = -1
    while True:
        i = text.find("<h2>", i + 1)
        j = text.find("</h2>", i + 1)
        if i == -1:
            break
        h2_pos.append((i + len("<h2>"), j))
    return h2_pos

def find_urls(text, cwd):
    urlreg = "(?P<url>https?://[^\s\"\'\)]+)"
    urls = re.findall(urlreg, text)
    urlreg2="(?<=(href=\"|src=\"))[/]*(?:[A-Za-z0-9-._~!$&'()*+,;=:@]|%[0-9a-fA-F]{2})*(?:/(?:[A-Za-z0-9-._~!$&'()*+,;=:@]|%[0-9a-fA-F]{2})*)*"
    urlreg2="(href=\"|src=\")([^\"\s]+)\""
    urlreg3="(\"[^\"\s]+.pdf\")"
    urls2 = [l[1] for l in re.findall(urlreg2, text)]
    urls3 = [l.replace("\"","") for l in re.findall(urlreg3, text)]
    urls2 += urls3
    for i, elem in enumerate(urls2):
        if elem[:1] == "/":
            urls2[i] = urlparse(cwd).scheme + "://" + urlparse(cwd).netloc + elem
    #        print(cwd, elem, urls2[i])
        elif not elem.startswith("http"):
            urls2[i] = cwd+elem
            #print(cwd, elem, urls2[i])
    #print(urls2)
    return urls2

#=============================================================================================================================================

def get_hpc(path):
    """
    todo: add folders for weeks
    """
    if not os.path.isdir(path):
        os.mkdir(path)

    text = download_bb_page("_237249_1",  "_3923023_1")
    h2_pos = find_h2s(text)

    endings = [".pdf", ".zip", ".jpg", ".png"]
    endings = []

    for i, (posi, posj) in enumerate(h2_pos):
        end_of_part = h2_pos[i+1][0] if i < len(h2_pos) - 1 else len(text)
        name_of_part = text[posi:posj]
        ddir = path + name_of_part.replace(" ", "_") + "/"
        download_links(text[posi:end_of_part], endings, ddir, cwd="https://www.ole.bris.ac.uk/webapps/blackboard/content/")

#get_hpc("/home/fecht/uni/sem5/hpc/")
