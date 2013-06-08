""" Download PA public death records """

import os
import re
import sys

import requests

# ex: <a href="indices - death/1906 Death/D-06 A-B.pdf">D-06 A-B.pdf</a><br>
PATTERN = re.compile(r'<a href=\"(?P<url>.*?)\">'
                      '(?P<filename>.*pdf)</a><br>')

# download up to chunk size bytes at once into memory:
CHUNK_SIZE = 1024 * 1024 * 1 # 1 MB


def download():
    basedir = os.path.join(os.environ["HOME"],
            "Documents/Genealogy/Sources/PA Vital Records/Death Index")
    if not os.path.exists(basedir):
        raise IOError(basedir + " does not exist.")

    baseurl = "http://www.health.state.pa.us/indices"
    yearurl = baseurl + "/%(year)d Death.htm"

    # starts in 1906, ends in 1962:
    for year in range(1906, 1963):
        print "Downloading year %(year)d:" % {'year': year}

        url = yearurl % {'year': year}
        r = requests.get(url)
        if r.status_code != 200:
            raise Exception("Fail: %s" % url)
        
        buf = r.text

        # create year directory to store files:
        d = os.path.join(basedir, str(year))
        if not os.path.exists(d):
            os.mkdir(d)

        # make a list of files to snag:
        for line in buf.split("\n"):
            if not line:
                continue

            m = re.match(PATTERN, line)
            if not m:
                raise Exception("Parse failure: %s" % line)

            gd = m.groupdict()
            fileurl = baseurl + "/" + gd['url']
            filename = gd['filename']

            sys.stdout.write("  %s: " % filename)

            filepath = os.path.join(d, filename)
            if os.path.exists(filepath):
                sys.stdout.write("Skipping\n")
                continue

            # don't have the file yet:
            tmp = os.path.join(basedir, "tmp.pdf")
            if os.path.exists(tmp):
                os.remove(tmp)

            # save to tmp first:
            r = requests.get(fileurl, stream=True)
            if r.status_code != 200:
                raise Exception("Failed to fetch %s" % fileurl)

            f = open(tmp, "wb")
            for buf in r.iter_content(chunk_size=CHUNK_SIZE):
                sys.stdout.write(".")
                sys.stdout.flush()
                f.write(buf)

            f.close()
            sys.stdout.write("\n")

            # move tmp to its real location:
            os.rename(tmp, filepath)


if __name__=='__main__':
    download()
