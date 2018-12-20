import requests
import os
import json
from io import StringIO


class Skylign(object):
    """Class for fetching HMM logos from the Skylign server

    http://skylign.org/help
    """

    base_url = "http://skylign.org"

    def _raw_submit_logo(self, hmm_file):
        """Upload a HMM file and get info about the resulting logo

        Response should contain the success message, url, and uuid.
        """
        #curl -H 'Accept:application/json' -F file='@hmm' -F processing=hmm http://skylign.org

        # accept either HMM string or file
        file = self._open_hmm(hmm_file)
        filename = os.path.basename(file.name) if hasattr(file, "name") else "query.hmm"
        files = {
            'file': (filename, file),
        }
        payload = {
            'processing': 'hmm',
        }
        req = requests.post(self.base_url, data=payload, files=files, headers={'Accept': 'application/json'})
        return req

    def submit_logo(self, hmm_file):
        """Upload a HMM file and get info about the resulting logo

        Response should contain the success message, url, and uuid.
        """
        req = self._raw_submit_logo(hmm_file)
        req.raise_for_status()

        response = json.loads(req.text)

        if "error" in response:
            raise Exception("Skylign Error", response, req)
        return response

    def _open_hmm(self, hmm):
        """Constructs a file-like object from various HMM specifications

        Accepts:
        - filenames
        - HMMER format strings (start with HMMER)
        - file-like objects

        Return:
        - A file-like object
        """
        if type(hmm) == str:
            hmm = os.path.expanduser(hmm)
            # Existing file
            if os.path.exists(hmm):
                return open(hmm, 'rb')
            # HMMER format
            if hmm[:5].casefold() == "hmmer":
                filelike = StringIO(hmm)
                filelike.name = "str.hmm"
                return filelike
            # fall back on filename
            return open(hmm, 'rb')
        else:
            # file-like objects
            return hmm

    def get_logo_url(self, hmm_file):
        """Upload a HMM file and get the URL for the resulting logo"""
        response = self.submit_logo(hmm_file)
        return response["url"]

    def get_logo(self, hmm_file):
        """Get a logo for an HMM. Returns a bytes object containing the PNG image"""
        #curl -H 'Accept:image/png' http://skylign.org/logo/6BBFEB96-E7E0-11E2-A243-DF86A4A34227 > 6BBFEB96-E7E0-11E2-A243-DF86A4A34227.png
        response = self.submit_logo(hmm_file)
        uuid = response["uuid"]

        # Can use the /logo endpoint with Accept:image/png for default image
        #url = response["url"]
        #req = requests.get(url, headers={'Accept':'image/png'})

        # /download endpoint provides additional control
        url = "{base}/download/{uuid}/image?colors=consensus&format=png".format(base=self.base_url, uuid=uuid)
        req = requests.get(url, headers={})
        req.raise_for_status()

        return req.content

    def save_logo(self, hmm_file, png_file):
        """Save the logo PNG to a file"""
        png = self.get_logo(hmm_file)
        with open(png_file, 'wb') as out:
            out.write(png)


def get_pfam(pfam_id):
    """Get a PFAM HMM as a string"""
    url = "http://pfam.xfam.org/family/{id}/hmm".format(id=pfam_id)
    req = requests.get(url)
    req.raise_for_status()
    return req.text
