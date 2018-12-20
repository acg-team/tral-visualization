"""repeatdiagram.py

Requirements:
    pip install biopython reportlab

"""

import colorsys
import math
import re
from reportlab.lib import colors
from Bio.Graphics import GenomeDiagram
from Bio.SeqFeature import SeqFeature, FeatureLocation


try:
    from scipy.constants import golden
except Exception:
    golden = (1 + 5**0.5)/2


def is_tral_repeat(repeat):
    "Duck-type for tral.repeat.repeat.Repeat instance"
    return (
            hasattr(repeat, 'begin') and
            hasattr(repeat, 'msa_original') and
            hasattr(repeat, 'repeat_region_length')
        )


class RepeatDiagram(object):
    """Diagram to """
    def __init__(self,tracks):
        """
        Args:
            tracks (list): List of tracks, ordered from top to bottom. Tracks may be either
                           SeqRecord objects, or (str,int) pairs giving an identifier and the
                           track length.
        """
        tracks = list(tracks) #accept generators

        self._trackindices = {}
        self._tracklens = [0]*len(tracks)
        for i,track in enumerate(tracks):
            trackid,tracklen = self._trackid(track)
            self._trackindices[trackid] = i
            self._tracklens[i] = tracklen
        self._repeats = [[] for i in range(len(tracks))] #2D list
        self.feature_options = dict(
                border=colors.lightgrey,
                label=True,
                label_position="start",
                label_size=10,
                label_angle=0)
        self.track_options = dict(
                greytrack=True,
                height=1,
                start=0)
        self.draw_options = dict(
                format="linear",
                x=0,y=0,yt=0,
                start=0,end=max(self._tracklens),
                fragments=1,
                fragment_size=1
        )

    def _trackid(self,track):
        """Try to guess the track ID. Works for strings, BioPython SeqRecords, and TRAL Sequences
        """
        if hasattr(track,"id"):
            return track.id, len(track)
        elif hasattr(track,"name"):
            return track.name, len(track)
        elif type(track) == tuple:
            return track
        else:
            # backup, could give bad lengths
            return str(track),len(track)
    def _trackindex(self,track):
        return self._trackindices[self._trackid(track)[0]]

    def _repeat_coords(self,repeat,strand=0):
        """Get coordinates for a varienty of repeat datatypes. Coordinates are 0-based half-inclusive,
        like python slice.

        Args:
            repeat: A repeat. Accepts
                - a tuple (int,int) giving start & end
                - a tuple (int,int,int) giving start, end, and strand

        Return:
            FeatureLocation

        """
        if type(repeat) == tuple:
            if len(repeat) == 2 and all(type(r) == int for r in repeat):
                return FeatureLocation(repeat[0],repeat[1],strand)
            elif len(repeat) == 3 and all(type(r) == int for r in repeat):
                return FeatureLocation(*repeat)
        #elif is_tral_repeat(repeat):

        raise ValueError("Unknown repeat type")

    def add_repeat(self,track,repeat,strand=0):
        """Add a repeat for a particular track
        """
        i = self._trackindex(track)
        self._repeats[i].append(self._repeat_coords(repeat,strand))

    def add_repeats(self,track,repeats,strand=0):
        #import pdb; pdb.set_trace()
        if is_tral_repeat(repeats):
            # TRAL Repeat object
            letters = re.compile("\w")
            start = repeats.begin-1
            for row in repeats.msa_original: #TODO msa or _original?
                l = sum([1 for c in row if letters.match(c)])
                self.add_repeat(track, (start,start+l,strand))
                #print("feature start={} len={} row={}".format(start,l,row))
                start += l
            # Check we used all the residues. If this fails try iterating .msa
            assert start == repeats.repeat_region_length+repeats.begin-1
        elif hasattr(repeats,"repeats"):
            # TRAL RepeatList
            for r in repeats.repeats:
                self.add_repeats(track,r,strand)
        else:
            # iterable of repeats
            for r in repeats:
                self.add_repeat(track,r,strand)

    def _create_feature_set(self,track,**feature_options):
        """Create a Track object for the specified track

        Args:
            track (str): track identifier
            **feature_options (mixed): additional options, passed to FeatureSet.add_feature().
                                       Overrides self.feature_options.

        Return:
            FeatureSet for the track
        """
        fs = GenomeDiagram.FeatureSet()
        tracknum = self._trackindices[track]
        for i,loc in enumerate(self._repeats[tracknum]):
            feature = SeqFeature(loc)
            options = dict(self.feature_options)
            options.update(feature_options)
            options.setdefault("color",self.rainbow(i))
            #options.setdefault("name",str(i+1))
            fs.add_feature(feature,**options)
        return fs

    def _create_track(self,track,track_options=None, feature_options=None):
        """Create a Track object for the specified track

        Args:
            track (str): track identifier
            **feature_options (mixed): additional options, passed to FeatureSet.add_feature(). Overrides self.feature_options.

        Return:
            FeatureSet for the track
        """
        i = self._trackindex(track)
        options = dict(self.track_options)
        if track_options:
            options.update(track_options)
        options.setdefault("name",track)
        options.setdefault("end",self._tracklens[i])

        if feature_options is None:
            feature_options = {}

        fs = self._create_feature_set(track, **feature_options)
        tr = GenomeDiagram.Track(**options)
        tr.add_set(fs)
        return tr

    def rainbow(self,i):
        hue = i*golden
        return colors.Color(*colorsys.hsv_to_rgb(hue,.5,1))

    def diagram(self,name="Repeat Diagram",size=(800,.25),draw_options=None,track_options=None,feature_options=None):
        """Construct a GenomeDiagram from the current set of repeats

        The size argument overwrites the 'pagesize' and 'orientation' parameters of draw_options
        so that the final image is the specified size. Furthermore, if the height is a float
        between 0 and 1, then it is interpreted as the aspect ratio (height/width) for a single track.

        Args:
            size (2-tuple):         (width,height)
            draw_options (dict):    arguments to pass to GenomeDiagram.draw
            track_options (dict):   arguments to pass to GenomeDiagram.Track
            feature_options (dict): arguments to pass to FeatureSet.add_feature
        """
        gd_diagram = GenomeDiagram.Diagram(name)

        for track,i in sorted(self._trackindices.items(),key=lambda x:x[1]):
            tr = self._create_track(track,track_options,feature_options)
            gd_diagram.add_track(tr,len(self._trackindices)-i+1)#order top to bottom

        options = dict(self.draw_options)
        options.setdefault("fragments",1)

        if size:
            w,h = size
            # accept height as the aspect ratio for each track
            if h < 1:
                aspect = h
                h = math.ceil(w*aspect*len(self._trackindices)*options["fragments"])
            options["pagesize"] = (w,h)
            options["orientation"] = "portrait" if w<h else "landscape"
        print("pagesize={pagesize}".format(**options))
        gd_diagram.draw(**options)
        return gd_diagram

    def image(self,**diagram_args):
        """Jupyter helper method for displaying the diagram"""
        from IPython.display import Image
        return Image(self.diagram(**diagram_args).write_to_string("PNG"))

    def save(self,filename,format="PNG",**diagram_args):
        self.diagram(**diagram_args).write(filename,format)

    def __repr__(self):
        names = sorted(self._trackindices.items(),key=lambda x:x[1])
        print( names)
        return "RepeatDiagram({0})".format(list(zip(map(lambda x:x[0],names),self._tracklens)))


def hsl_to_html(h,s=1,l=1):
    "Convert hsl color to an HTML color"
    rgb = colorsys.hsv_to_rgb(h, s,l)
    return '#%02x%02x%02x' % tuple([int(c*255) for c in rgb])


def assign_HMM_colors(hmm):
    """Assigns an HTML color to each state of an HMM

    Follows a gradient from blue to red, with N and C states as grey."""
    n_cols = hmm.l_effective

    colmap = {'N': hsl_to_html(0,0,.5), 'C': hsl_to_html(0,0,.5)}
    for i,state in enumerate(hmm.insertion_states):
        colmap[state] = hsl_to_html((n_cols-i-1)*240./360./(n_cols-1), .3, 1.)
    for i,state in enumerate(hmm.match_states):
        colmap[state] = hsl_to_html((n_cols-i-1)*240./360./(n_cols-1), 1., 1.)
    return colmap


def show_hmm_state(hmm, seq, viterbi=None, width=None, trim=[],style=""):
    """Annotate a sequence with colors corresponding to HMM states

    Args:
        hmm (HMM): HMM, used to extract states

        seq (string): sequence

        viterbi (list of states): sequence of states for each residue in seq.
            If omitted, calculated with hmm_viterbi.viterbi.

        width (int): Wrap sequence with this number of characters per line. default: don't wrap

        trim (list of states): Set of states to ignore. trim=['N','C'] is often useful.

        style (string): extra style arguments to include
    Returns:
        An IPython HTML object, suitable for displaying in jupyter notebooks
    """
    from IPython.display import HTML

    colmap = assign_HMM_colors(hmm)
    if viterbi is None:
        viterbi = hmm_viterbi.viterbi(hmm,seq)
    span = "<span style='font-family:monospace;background: {color};{style}'>{aa}</span>"
    spans = [span.format(color=colmap[state],aa=aa,style=style) for state,aa in zip(viterbi,seq) if state not in trim]
    if width:
        spangroups = ["".join(spans[i*width:(i+1)*width]) for i in range(len(spans)//width+1)]
        return HTML("<br/>".join(spangroups))
    else:
        return HTML("".join(spans))

