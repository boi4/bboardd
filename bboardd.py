#!/usr/bin/env python3
import time
import os
import sys

from urllib.parse import urlparse
from math import gcd


import scraper

from auth import Auth



class Bboardd:

    def __init__(self,
            update_interval=30*60,
            update_old_interval=60*60*6,
            auth_file="{}/.config/bboardd/uob_login.txt".format(os.environ.get("HOME")
                if os.environ.get("HOME") is not None else ""),
            course_file="{}/.config/bboardd/courses.csv".format(os.environ.get("HOME")
                if os.environ.get("HOME") is not None else ""),
            base_dir=os.environ.get("HOME") if os.environ.get("HOME") is not None else "",
            headers=Auth.DEFAULT_HEADERS,
            ):
        self.update_interval = update_interval
        self.update_old_interval = update_old_interval
        self.auth_file = auth_file
        self.course_file = course_file
        self.base_dir = base_dir
        self.headers = headers
        self.sleep_time = 0
        self.session = None


    def run(self):
        ui = self.update_interval
        uoi = self.update_old_interval
        g = gcd(ui, uoi)
        while True:
            # prefer update_old to normal updates
            if self.sleep_time % uoi == 0:
                self.update_files(update_old = True)
            elif self.sleep_time % ui == 0:
                self.update_files(update_old=False)
            time.sleep(g)
            self.sleep_time += g

    def get_contents(self):
        with open(self.course_file, "r") as f:
            l = [line.split(",") for line in f.read().split("\n")]
        return [content for content in l if len(content) == 3]

    def update_files(self, update_old=False):
        a = Auth()
        a.login()
        self.session = a.get_session()
        self.headers = a.get_headers()
        content_pages = self.get_contents()
        print("Content Pages")
        print("="*40)
        print(content_pages)
        print("")

        for path, course_id, content_id in content_pages:
            download_dir = "{}/{}".format(self.base_dir, path)
            print("Downloaddir: {}".format(download_dir))
            if course_id == "_237247_1":
                self.get_ml(download_dir)
                continue
            if course_id == "_237249_1":
                self.get_hpc(download_dir, update_old)
                continue
            if not os.path.isdir(download_dir):
                os.mkdir(download_dir)
            endings = [".pdf", ".zip"]
            #endings = []

            text = scraper.download_bb_page(self.session, self.headers, course_id, content_id)

            self.download_urls(text, endings, download_dir,
                    update_old=update_old, url_cwd="https://www.ole.bris.ac.uk/webapps/blackboard/content/")


    def download_urls(self, text, endings, ddir, update_old=True, url_cwd=""):
        if ddir[-1:] != "/":
            ddir += "/"

        urls = scraper.find_urls(text, cwd="https://www.ole.bris.ac.uk/webapps/blackboard/content/")

        #if ((not any(url.endswith(ending) for ending in endings for url in urls)) or endings == []) and not any( url.split("/")[-1].startswith("xid") for url in urls):
            #return
        if not os.path.isdir(ddir):
            os.mkdir(ddir)
        #print("\n" + ddir)
        #print("\n".join(urls))

        for url in urls:
            if url.split("/")[-1].startswith("xid"):
                r = self.session.get(url, headers=self.headers, allow_redirects=False)
                loc = r.headers.get("Location")
                base = urlparse(url).scheme + "://" + urlparse(url).netloc
                if not loc:
                    print("could not download {}".format(url), file=sys.stderr)
                    continue
                if loc.split("/")[-1].endswith(".html") and any(url in line and "iframe" in line for line in text.split("\n")):
                    r = self.session.get(base+loc, headers=self.headers)
                    self.download_urls(r.text, endings, ddir, url_cwd="/".join((base+loc).split("/")[:-1])+"/")
                    continue
                self.download_file(base + loc, ddir, skipexisting=(not
                    update_old), overwrite=True)
            elif url.endswith(".html") and any(url in line and "iframe" in line for line in text.split("\n")):
                r = self.session.get(url, headers=self.headers)
                self.download_urls(r.text, endings, ddir, url_cwd="/".join(url.split("/")[:-1])+"/")
                continue
            elif any(url.endswith(ending) for ending in endings) or endings==[]:
                self.download_file(url, ddir, skipexisting=(not update_old), overwrite=True)


    def download_file(self, url, save_path, overwrite=False, skipexisting=False):
        print(overwrite)
        if url[-1:] == "/" or url.count("/") == 2:
            print("Not downloading {} is directory".format(url), file=sys.stderr)
            return
        if save_path[-1:] == "/" or os.path.isdir(save_path):
            save_path = save_path + "/" + url.split("/")[-1]
        if skipexisting and os.path.isfile(save_path):
            print("skipping {}".format(url))
            return
        while (not overwrite) and os.path.isfile(save_path):
            save_path = save_path + "_"
        print("Downloading {} to {}".format(url, save_path))
        r = self.session.get(url, stream=True, headers=self.headers)
        with open(save_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)


    def get_ml(self, path):
        os.system("git -C {} pull".format(path))

    def get_hpc(self, path, update_old):
        """
        todo: add folders for weeks
        """
        if not os.path.isdir(path):
            os.mkdir(path)

        text = scraper.download_bb_page(self.session, self.headers, "_237249_1",  "_3923023_1")
        h2_pos = scraper.find_h2s(text)

        endings = [".pdf", ".zip", ".jpg", ".png"]
        endings = []

        for i, (posi, posj) in enumerate(h2_pos):
            end_of_part = h2_pos[i+1][0] if i < len(h2_pos) - 1 else len(text)
            name_of_part = text[posi:posj]
            ddir = path + "/" + name_of_part.replace(" ", "_") + "/"
            self.download_urls(text[posi:end_of_part], endings, ddir,
                    update_old=update_old, url_cwd="https://www.ole.bris.ac.uk/webapps/blackboard/content/")


def main():
    b = Bboardd(base_dir="{}/uni/sem5".format(os.environ.get("HOME")))
    b.run()

if __name__ == "__main__":
    main()
