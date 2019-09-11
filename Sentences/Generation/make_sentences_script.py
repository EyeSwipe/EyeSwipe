import os
import re
import sys
import html
import datetime
import unicodedata

import videolist as vlist
import gen_consts as gconsts

# import 'sentence_consts' from .. as 'sconsts'
from os.path import abspath, join, dirname
sys.path.append(abspath(join(dirname(abspath(__file__)), '..')))
import sentence_consts as sconsts

# There are some subtitles that have been found through manually looking
# at the set that appear to be complete garbage. That list is here:
#
# Reasons:
#  (0) gibberish (different language?)
#  (1) final timestamp is at 27 HOURS  <-- WTF?
garbage_subs = {'1M5r_B1_WZ8', 'P6ODTQKhaXk'}

# If True, this will instead output to a separate file, where we can
# find the videoID associated with each sentence
debug = True
debug_file = join(dirname(abspath(__file__)), 'DEBUG_SENTENCES.txt')

# load the lexicon, for later
with open(sconsts.lexicon_file) as f:
    lexicon = set(f.read().split('\n'))

file = gconsts.all_sentences if not debug else debug_file
if os.path.exists(file):
    os.remove(file)

def write_sentences(videoID, sentences):
    with open(file, 'a+') as f:
        if debug:
            f.write(videoID + '\n')
            sentences = ['\t' + s for s in sentences]
        f.write('\n'.join(sentences) + '\n')

# ***********************************************************
# NOTES ON FORMATTING
# ***********************************************************

# all subtitles start with the following:
"""
WEBVTT
Kind: captions
Language: en
"""
# The rest of the file then looks like this:
"""
00:00:27.760 --> 00:00:30.129
Trump's presidency
is like one of his handshakes.

00:00:30.229 --> 00:00:33.032
It pulls you in,
whether you like it or not.

00:00:33.833 --> 00:00:36.402
He's had so many
terrible moments this year,

00:00:36.502 --> 00:00:38.137
you probably forgot about
many of them.
"""
# Taken from videoID: '1ZAPwfrtAFY'
#
# There are a few other formatting points:
# * Subititles support html formatting (e.g. <i>foo</i>)
#   * As such, some html characters are escaped. The most common ones
#     are '&lt;' and '&gt;'
# * ALL SUBTITLES END WITH TWO BLANK LINES. This is an important detail
# * Styles differ across channels and videos, so here's a list of edge
#   cases that must be accounted for:
#   * Escaped phrases or descriptions, e.g. [Laughter]
#   * Rolling text -- each block contains overlap with the previous to
#     give the impression of text rolling up the screen
#   * Additional formatting on the first line of the blocks, such as:
#       00:00:03.536 --> 00:00:04.303 align:start position:0%
#   * (Mostly) Empty lines within blocks (we can't just split by '\n\n')
#     * They won't be completely empty, as far as I can tell: they all
#       have -- at the very least -- spaces on those lines
#   * '>>' to denote a change in speaker
#   * '$Name: Text' or '($Name) Text' to denote who's talking
#     * Note: These two will sometimes be used in combination, but only
#       use a named switch for certain people, not others. For an
#       example, see this videoID: W7SZmMW6Ow0
#   * 'Cues', which prefix blocks with a number, starting at 1 and
#     counting up. Example:
"""
        WEBVTT
        Kind: captions
        Language: en

        1
        00:00:00.000 --> 00:00:05.580
        [MUSIC]

        2
        00:00:05.580 --> 00:00:06.396
        That's not his briefcase.
"""
#   * All-caps (sometimes even while $Name is normally cased)
# ***********************************************************

class TextGroup():
    def __init__(self, lines, start_time, end_time):
        self.lines = lines
        self.start_time = start_time
        self.end_time = end_time

    def from_text(time_header, body):
        lines = body.split('\n')

        # Get the time from the header. The header is guaranteed to be
        # formatted like:
        #   00:00:00.000 --> 00:00:05.580
        # even though they may be formatted differently in the raw text
        # of the subtitles themselves:
        #   00:00:03.536 --> 00:00:04.303 align:start position:0%

        start, end = time_header.split(" --> ")

        time_fmt = "%H:%M:%S.%f"
        start_time = datetime.datetime.strptime(start, time_fmt)
        end_time = datetime.datetime.strptime(end, time_fmt)

        lines = [replace_html_escaped_chars(l) for l in lines]

        return TextGroup(lines, start_time, end_time)

    def time_diff(a, b):
        # returns the amount of time, in seconds, between the end of `a`
        # and the start of `b`, as a float.
        
        return (b.start_time - a.end_time).total_seconds()

    def join(a, b, merge_overlap=True):
        # combines `a` and `b` into one `TextGroup`.
        #
        # if merge_overlap is True (default), then it we'll treat the
        # overlapped region as expected -- it'll only appear once.
        #
        # NOTE: This does not take into account the time difference
        # between the two groups

        new_lines = []

        if merge_overlap:
            def non_empty_line(l):
                return re.match(r"^\s*$", l) is None

            b.lines = list(filter(non_empty_line, b.lines))

            new_lines = a.lines + b.lines[TextGroup.overlap(a, b):]
        else:
            new_lines = a.lines + b.lines

        start = a.start_time
        end = b.end_time

        return TextGroup(new_lines, start, end)

    def overlap(a, b):
        # gives the number of lines that overlap between the two groups,
        # where `b` starts with the end of `a`
        #
        # I have only ever seen this done with Jimmy Kimmel's videos,
        # but he has reached the trending page an unfortunate number of
        # times.
        #
        # Here's an example videoID to take a look: eIp7PYuAu0k

        if len(a.lines) == 0 or len(b.lines) == 0:
            return 0

        # check if `a` contains the ending string of `b`
        if b.lines[0] not in a.lines:
            return 0

        # the starting line of the overlap
        start_index = a.lines.index(b.lines[0])

        # verify that the rest of the lines are the same
        overlap_size = 1
        for a_line, b_line in zip(a.lines[start_index+1:], b.lines):
            if a_line != b_line:
                return 0

            overlap_size += 1

        return overlap_size

    def overlaps(a, b):
        # Returns whether or not the two groups have any overlap,
        # irrespective of the time difference between them

        return TextGroup.overlap(a, b) != 0


def subtitle_uses_overlap(groups):
    # Determines whether or not the subtitles for a video overlap groups
    # in order to give a scrolling effect

    n_with_overlap = 0
    n_small_gap = 0
    for a, b in zip(groups, groups[1:]):
        if TextGroup.time_diff(a, b) < gconsts.subtitle_max_gap_time:
            n_small_gap += 1
            if TextGroup.overlaps(a, b):
                n_with_overlap += 1

    if n_small_gap == 0:
        return False

    fraction_with_overlap = n_with_overlap / n_small_gap
    
    return fraction_with_overlap >= gconsts.subtitle_min_fraction

def read_groups(videoID):
    # returns a list of `TextGroup`s corresponding to the videoID. If no
    # file is found, then it returns None

    # get the file for the videoID. The file format is:
    # $VIDEOID.en.vtt
    # but we're using gen_consts.ext to cover for the last bit
    filepath = os.path.join(gconsts.subtitles_dir, "{}.{}".format(videoID, gconsts.ext))
    if not os.path.exists(filepath):
        return None

    with open(filepath) as f:
        # The first block is the header, which looks something like this:
        """
        WEBVTT
        Kind: captions
        Language: en
        """
        # So we don't include the first block.
        #
        # We'd like to be able to split by '\n\n', but ONE subtitle
        # doesn't adhere to this format. SO, we'll use a more complex
        # solution that doesn't rely on a usually-adhered-to style for
        # writing the subtitles, and instead use the specification of
        # the format itself

        time_fmt = r"[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}"
        time_line = r"({} --> {})[^\n]*\n".format(time_fmt, time_fmt)

        pattern = r"(\n\d+)?\n{}(([^\n]*\n?)*?)(?=\n(\d+\n)?{}|$)"

        # pattern = r"(?:(?:\n\d+)?\n){}((?:[^\n]*\n)*?)(?=({})|$)"
        pattern = pattern.format(time_line, time_line)

        blocks = re.finditer(pattern, f.read())

        # Group 2 is the first time range, group 3 is the body of text
        blocks = list(map(lambda m: (m.group(2), m.group(3)), blocks))

    return [TextGroup.from_text(b[0], b[1]) for b in blocks]

def replace_html_escaped_chars(s):
    # remove html tags
    s = re.sub(r"<.+?>", "", s)
    s = re.sub(r"</.+?>", "", s)

    # Replace the various escaped characters
    return html.unescape(s)

def preprocess_groups(groups):
    # Takes a list of `TextGroup`s and does a few key things:
    # * If the subtitles are formatted to have overlaps
    #   (see list above), groups that overlap are combined
    # * Returns a list of time groups. We're defining time groups as
    #   sets of sequential subtitle groups that have are effectively
    #   continuous, i.e. there is no gap greater than the maximum gap
    #   time, as defined in 'gen_consts.py'
    #   * The list that is returned is a list of lists of lines, where
    #     we have concatenated the lists of lines within the indiviual
    #     subtitle groups into one time group.
    
    if len(groups) == 0:
        return []

    # Distinct groupings, determined by the amount of time between
    # groups. Any gap greater than `gconsts.subtitle_max_gap_time` will
    # be used to indicate a different time group.
    time_groups = [groups[0]]
    
    for g in groups[1:]:
        last_group = time_groups[-1]

        if TextGroup.time_diff(last_group, g) > gconsts.subtitle_max_gap_time:
            time_groups.append(g)
            continue

        time_groups[-1] = TextGroup.join(last_group, g)

    return time_groups

# charset = r"a-zA-Z0-9.\'\"\-,;:?! "

def format_line(line, urls=None):
    # Formats a line for use in to_sentences()
    #
    # This function only exists to separate certain parts of
    # `to_sentences()`, so many pieces of this function only make sense
    # when understood within the context of the other.
    #
    # <speaker> will always indicate a new speaker (but will not catch
    # all of them)
    #
    # <char> indicates a character that is outside of our character set
    #
    # PLEASE NOTE: Quotations are not removed -- that will be done later
    # because they often cross lines.

    # Do a couple standardizing things -- both with whitespace and
    # dashes. All whitespace is converted to a single space, and all
    # dash-like characters are converted to '-'
    l = re.sub(r"\s+", " ", line)
    # left side is en dash, right side is em dash
    l = re.sub(r"(–|—)", "-", l)

    # remove accents -- borrowed from a stackoverflow post:
    # https://stackoverflow.com/a/31607735
    # l = unicode(l)
    l = unicodedata.normalize('NFD', l)
    l = l.encode('ascii', 'ignore')
    l = l.decode('utf-8')

    # Remove and store any urls. This pattern is heavily inspired by the
    # one found at https://stackoverflow.com/a/3809435
    # This one isn't perfect, and needed to be modified slightly to
    # avoid matching on acronyms, but it should be good.
    url_pattern = r"([-a-zA-Z0-9]+:(//)?)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{2,6}\b([-a-zA-Z0-9()@:%_+.~#?&/=]*)"
    def replace_url(match):
        if urls is None:
            return "<url>"
        else:
            # group 0 is the entire string
            index = len(urls)
            urls.append(match.group(0))
            return "<url-{}>".format(index)
    l = re.sub(url_pattern, replace_url, l)

    # We'll do a small thing here that should aid in readability.
    # Because percentages often follow a predictable format, we'll
    # replace them with 'percent'
    l = re.sub(r"(?<=\d)%", " percent", l)

    # Remove all characters that won't:
    #   A: Be a part of the final sentence, or
    #   B: Help inform sentence boundaries
    # We'll replace those charactrs with '<char>' to indicate that there
    # was an unsupported character in its place.
    #
    # Two characters we specifically NEED to remove are open and close
    # angle brackets ('<', '>'), because we use them in tags. We've
    # already made one tag with them -- '<url>', so we want to replace
    # unsupported characters EXCEPT where they are being used as part of
    # '<url>'.
    #
    # The regex pattern we're using is more complicated than I'd like,
    # but it seems to be the best solution (others require more helper
    # functions). URL tags are not fixed width -- it may also be of the
    # form '<url-$N>', where $N is an unbounded non-negative integer.
    # Because of this, we can't use a lookbehind assertion to only match
    # the text in-between, so we include url tags at the start of our
    # match. The replacement of characters then operates on the second
    # match group, while we preserve the first. The rest of the regex
    # should be *fairly* self-explanatory. 
    keep_in = r"a-zA-Z0-9.\'\"\-,;:?!()\[\]*'\" "

    def repl_chars(match):
        return match.group(1) + re.sub("[^{}]+".format(keep_in), "<char>", match.group(2))
    #
    l = re.sub(r"(^|<url(?:-\d+)?>)(.*?)($|(?=<url(-\d+)?>))", repl_chars, l)

    # Remove some speaker annotations. There's a few different ways this
    # is done that we need to take care of here (others will be
    # inadvertently taken care of later)
    #
    # What are speaker annotations? It's a term I made up (although that
    # may be what it's actually called). It refers to the times in a
    # subtitle in which a change in who's speaking labels them by name.
    # There are a few different ways this is done. Here are some
    # examples, in the time blocks that they originally were in:
    """
    00:00:52.052 --> 00:00:58.391 align:start size:88% position:13%
    &gt;&gt; Stephen: GOOD TO SEE YOU
    TOO.
    *********************
    00:00:14.530 --> 00:00:16.460
    (Garrett) There's no way that's correct!
    *********************
    00:00:00.100 --> 00:00:02.040
    STEVE (VO): Obviously, I love James.
    
    <...>

    00:02:10.020 --> 00:02:11.960
    DR. PLIER: For it was camouflage.
    *********************
    00:00:08.000 --> 00:00:10.000
    G: Hi guys, I'm here with my mom! T: Hey!
    *********************
    00:00:02.250 --> 00:00:03.203
    - [Group Member] Hey, puppy!

    <...>

    00:00:18.480 --> 00:00:20.477
    - Hi, BuzzFeed, we're BTS with--

    00:00:20.650 --> 00:00:22.490
    - Hi, BTS!
    - PPS, the puppies.
    """
    # Videos (in order): 2GrKY7Qqal8, -RmUADCWI4A, 0I9vWjc9nao,
    # 0PW9MWDWLH8, 1PhPYr_9zRY
    #
    # Some of these (like the second-to-last exmaple) cannot be done
    # yet, as they require other knowledge about sentence boundaries to
    # remove.
    #
    # For those that don't, however, we CAN get rid of them. We'll
    # ingore speakers switching mid-line for now, and just focus on
    # when it starts the line

    parenthetical = r"(\([^\)]*\)|\[[^\]]*\])"

    name = r"[A-Z]([-a-z]+((\. ?| )[A-Z][-a-z]*)*|[-A-Z]+((\. ?| )[-a-z]+)*)?"

    pattern = r"^( ?(<char>|-))? ?{}( {})?: ".format(name, parenthetical)
    #             \-------------/ / \----/
    #                 spacing     |    \--parentheticals
    #                            name
    l = re.sub(pattern, "<speaker>", l)

    # collapse tags
    l = re.sub(r"(<[^>]*>) (?=<[^>]*>)", r"\1", l)

    return l

def to_sentences(time_groups):
    # Picks out sentences from the lines
    
    lines = [[format_line(l) for l in group.lines] for group in time_groups]

    # `format_line` contains plenty of information as to what formatting
    # has been done to the lines at this point. Notably, a couple
    # characters and sequences have been replaced with '<...>'. The
    # first part of this establishes the rest of that
    #
    # We'll apply the same process for every group

    all_sentences = []

    for g in lines:
        # add the lines back together so that we can deal with one
        # coherent string
        s = '\n'.join(g)

        # Remove various parenthetical statements: '(foo)', '[foo]', and
        # *foo* (or **foo**). These typically are used to convey
        # information other than what's being said - which is what we
        # care about.
        #
        # Additionally (as mentioned above, in `format_line()`)
        # parenthesis can also denote a new speaker, so we'll note that
        # as well
        s = re.sub(r"\([^\)]*?\)", "<paren>", s)
        s = re.sub(r"\[[^\]]*?\]", "<bracket>", s)
        s = re.sub(r"(\*+)[^*]*?\1", "<asterisk>", s)

        # Instead of removing the inside of quotes, we'll just mark
        # them. Double quotes are easy, because they don't get used in
        # any other circumstance than as quotation, but single quotes
        # use the same character as apostrophes, so it needs to be
        # marginally more complicated.
        s = re.sub(r"\"([^\"]*?)\"", r"<dquote>\1</dquote>", s)
        #
        single_pattern = r"(?<=\s)__'([^']*?)'__(?![A-Za-z])"
        s = re.sub(single_pattern, r"<squote>\1</squote>", s)

        # ************************************************************
        # The next thing that we need to do is heavily inspired from a
        # certain stackoverflow answer about how to split a text into
        # sentences. We're essentially using it as a way to keep track
        # of all of the special cases that we get in the English
        # language.
        #
        # Answer: https://stackoverflow.com/a/31505798
        #
        # we'll be using '<prd>' to mark periods while we temporarily
        # take them out

        # mark certain words that are able to have periods after them in
        # normal sentences.
        #
        # `amb` for ambiguous
        amb = ['Mr', 'Ms', 'Mrs', 'St', 'Dr', 'Prof', 'Capt', 'Lt',
               'Mt', 'Inc', 'Ltd', 'Co', 'Jr', 'Sr', 'Gov', 'Esq',
               'Hon', 'Rev']
        # we include '>' before in case of some other tag before it
        pattern = r"(?<=[\s^>])({})\.".format("|".join(amb))
        s = re.sub(pattern, r"\1<prd><maybe>", s, flags=re.IGNORECASE)

        # PhD is a special case:
        s = re.sub(r"(?<=[\s^])Ph\.D\.", r"Ph<prd>D<prd><maybe>", s)

        # Another special case is 'Vs.' or 'v.' in both lower and upper
        # case, which we know should not end a sentence
        #
        # This often occurs when talking about competitions or court
        # cases.
        s = re.sub(r"(?<=[\s^])(vs?)\.", r"\1<prd>", s, flags=re.IGNORECASE)

        replace_prd = lambda match: match.group(0).replace('.', '<prd>')

        # Deal with acronyms
        replace_prd_acronym = lambda match: replace_prd(match) + '<maybe>'
        #
        s = re.sub(r"([A-Z]\.){2,}", replace_prd_acronym, s)
    
        # Handle ellipsis
        s = re.sub(r"\.{3,}", r"<dots>", s)
        s = re.sub(r"(?<=[\s^])(?=<dots>)", "<maybe>", s)
        s = re.sub(r"(?<=<dots>)(?=[\s<$])", "<maybe>", s)
        
        # Handle numbers
        s = re.sub(r"\d+\.\d+", replace_prd, s)
        # Handling commas covers both European '5,6' (= 5.6) and
        # '2,019'
        replace_comma = lambda match: match.group(0).replace(',', '<comma>')
        #
        s = re.sub(r"(?<=[\s^])\d+(, ?\d+)+", replace_comma, s)

        # Handle dashes (we've converted all types of dashes to '-').
        # Dashes used as punctuation will have a space bfore or after
        s = re.sub(r"(\s)-", r"\1<maybe><dash>", s)
        s = re.sub(r"-(\s)", r"<dash><maybe>\1", s)


        # LAST STEP:
        #
        # Handle punctuation and use periods to mark sentence boundaries
        s = re.sub(r"([.!?])(</(?:s|d)quote>)", r"\1<stop>\2<maybe>", s)
        s = re.sub(r"([.!?])(?=[\s<$])", r"\1<stop>", s)
        # NOTE : We're discarding everything in the quotes because we're
        # not sure that it's a complete sentence
        s = re.sub(r"(?<![,.!?])(</(?:s|d)quote>)", r"<discard>\1<maybe>", s)

        # Another bit about quotes:
        # If the part of the sentence before the start of the quote
        # doesn't properly end, then we need to mark it for being
        # discarded.
        #
        # We're defining a lack of proper ending as not having
        # punctuation that would indicate such an ending.
        s = re.sub(r"(?<!<stop>)(\s+<(?:s|d)quote>)", r"<discard>\1", s)

        # Mark cases of URLs and unknown characters at the end of the
        # line with '<maybe>', because they might be used to terminate
        # the sentence
        s = re.sub(r"(<char>|<url(?:-\d+)>)(?=\n)", r"\1<maybe>", s)        

        # Commas imply that there's more to the sentence, so we'll use
        # '<continue>' to indicate that.
        s = re.sub(r",", r",<continue>", s)

        # make sure we don't get repeats of '<maybe>'
        s = re.sub(r"(<maybe>\s?){2,}", '<maybe>', s)

        # ************************************************************
        # USE THE MARKERS TO SPLIT INTO SENTENCES
        # ************************************************************
        s = s.replace('<stop>', '<maybe><new>')
        s = re.sub(r"(<maybe>\s?){2,}", '<maybe>', s)
        temp = [m.strip() for m in s.split('<maybe>')]

        s = ""
        last_fragment = None
        def shift_new_sentence(sentence):
            nonlocal s, last_fragment

            if last_fragment is not None:
                s += last_fragment + '<stop>'
            last_fragment = sentence
            return

        # m = current segment
        # p = previous
        for m, p in zip(temp, [""]+temp):
            # For each sentence block indicated by '<maybe>', we'll
            # attempt to determine whether or not it is a new sentence
            # or a part of the previous.
            #
            # This part is complicated.
            #
            # For reference, here's a list of all of the tags are
            # currently in use
            # * url | url-$N
            # * char
            # * continue
            # * speaker
            #     -- only at the beginning of a line
            # * discard
            # * paren | bracket | asterisk
            # * dquote | /dquote
            #     -- open and close like html tags 
            # * squote | /squote
            #     -- open and close like html tags
            # * maybe
            # * new
            # * comma
            # * prd
            # * dash
            # * dots
            # Note that the following tags have already been replaced:
            # * stop
            #
            # Rules that we're going to apply, in order of preference:
            # 1. <new> - if present - will be at the start of the string
            #    and will indicate the start of a new sentence
            # 2. <continue> at a sentence boundary should guarantee that
            #    the current sentence fragment will be added to the last
            # 3. <speaker> indicates the start of a new sentence
            # 4. If (1) and (2) conflicts with (3), the sentence will be
            #    joined with the last fragment and marked for being
            #    discarded.
            # 5. Sentences with <char> or <url> between words should be
            #    discarded
            # 6. However: <url> or <char>, if at the start or the end,
            #    will indicate a sentence boundary. 
            # 7. <paren>|<bracket>|<asterisk> are ignored if in the
            #    middle or end and used as a sentence boundary if at
            #    the start.
            # 8. <discard> will be done after the sentence has been
            #    completed and indicates that it should be thrown out
            # 9. All other escaped tags are ignored because they have
            #    already been taken into consideration.

            # Rule 1
            isNewSentence = m.startswith('<new>')

            # Rule 2
            if not isNewSentence:
                # Check for '<speaker>' in the starting tags
                if re.match(r"^(<[^>]*>\s?)*<speaker>", m) is not None:
                    isNewSentence = True

            # Rule 3
            continued = re.match(r"<continue>(<[^>]*>\s?)*$", p) is not None

            # Rule 4
            bypass_add_later = False
            if continued and isNewSentence:
                m = '<discard>' + m
                isNewSentence = False
                bypass_add_later = True

            # Rule 5 - we'll attempt to match the entire string
            tag = r"(?:<[^>]*>\s?)"
            other_tag = r"(?:<(?!url(?:-\d+)?|char)[^>]+>\s?)"
            word = r"(?:[\w,.;:!?]+\s?)"
            url_or_char = r"(?:<url(?:-\d+)?>|<char>)"
            
            """
            edge = r"{}*{}\s?(?:{}|{}\s?)*"
            start = edge.format(tag, word, word, other_tag)
            end = edge.format(tag, word, word, tag)
            pattern = r"^({}{})(\s?{})$".format(edge, url_or_char, edge)
            
            m = re.sub(pattern, r"\1<discard>\2", m)
            """

            start = r"(?=({}*))\2{}\s?(?=((?:{}|{})*))\3".format(tag, word, word, other_tag)
            end = r"(?=({}*))\5{}\s?(?=((?:{}|{})*))\6".format(tag, word, word, tag)

            pattern = r"^({}{})(\s?{})$".format(start, url_or_char, end)

            m = re.sub(pattern, r"\1<discard>\4", m)

            # follow through with rules 1 and 2
            if isNewSentence:
                shift_new_sentence(m)
                continue

            # Rule 6 (ending)
            pattern = r"^(<url(-\d+)?>|<char>)\s?(<[^>]*>\s?)*$"
            if re.match(pattern, p) is not None:
                shift_new_sentence(m)
                continue

            # Rule 6 (starting) and 7
            pattern = r"^(<[^>]*>\s?)*" +\
                      r"<(url(-\d+)?|char|paren|bracket|asterisk)>"
            if re.match(pattern, m) is not None:
                shift_new_sentence(m)
                continue

            # Now, it's just up to whether or not the fragment is the
            # start of a new sentence
            #
            # We'll only indicate that it's the start of a new sentence
            # if these conditions are met:
            #  (1) the fragment starts with a word that starts with an
            #      uppercase letter
            #  (2) the word appears in the lexicon as lowercase but not
            #      uppercase
            #
            # Regex to find the first word, so long as it starts with a
            # capital letter. The word will be the first match group.
            pattern = r"^(?:<[^>]*>\s?)*" +\
                      r"([A-Z][a-zA-Z]*)"
            match = re.match(pattern, m)
            if match is not None and not bypass_add_later:
                word = match.group(1)

                lower_in = word.lower() in lexicon
                upper_in = (word in lexicon or
                            (word[0] + word[1].lower()) in lexicon if len(word) > 1 else False)

                if lower_in and not upper_in:
                    isNewSentence = True

                # if (word.lower() in lexicon and
                #     not (word in lexicon or
                #          (word[0] + word[1].lower()) in lexicon
                #         )
                #    ):
                #     isNewSentence = True

            if isNewSentence:
                shift_new_sentence(m)
            else:
                if last_fragment is None:
                    last_fragment = m
                else:
                    last_fragment += " " + m

        if last_fragment is not None:
            s += last_fragment

        # Now that we've done essentially everything we needed to, we'll
        # start putting things back
        #
        # Every single tag is handled here.
        s = s.replace('<comma>', ',').replace('<prd>', '.')
        s = s.replace('<dash>', '-').replace('<dots>', '...')
        
        # We actually want to remove quotes, because we don't support
        # typing quotes
        s = re.sub(r"</?squote>", "", s)
        s = re.sub(r"</?dquote>", '', s)

        s = s.replace('<paren>', "").replace('<bracket>', "")
        s = s.replace('<asterisk>', "")

        # Remove helper control flow tags
        s = s.replace('<new>', "").replace('<continue>', "")
        s = s.replace('<speaker>', "")

        # For this case, we're removing URLs. Alternatively, we could
        # choose to save them
        s = re.sub(r"<url(-\d+)?>", "", s)

        # We're also going to remove unrecognized characters
        s = s.replace('<char>', "")

        sentences = s.split('<stop>')

        # standardize whitespace
        sentences = [re.sub(r"\s+", r" ", s.strip()) for s in sentences]

        # discard all sentences marked for being discarded
        sentences = list(filter(lambda s: '<discard>' not in s, sentences))

        all_sentences.extend(sentences)

    return all_sentences

def filter_sentences(sentences):
    def is_good(s):
        return re.match(r"\w", s) is not None

    return list(filter(is_good, sentences))

def ensure_lowercase(sentence):
    # If the given sentence is all uppercase, it converts it to
    # normal case, and if it is lowercase, it is left as is. There are
    # limitations to this, but this is a best attempt. A possible change
    # could be to put sentences that are only uppercase into a different
    # pool for later, as the casing may not be accurate.
    #
    # This will also remove any excess whitespace or certain punctuation
    # from the beginning and end of the sentence

    sentence = re.sub(r"(^[ \-]+|[ \-]+$)", "", sentence)

    # We'll essentially find all distinct words and if there is at least
    # one lowercase word, we'll say that the sentence is already in
    # lowercase.
    #
    # Note: Because we substitute '%' for 'percent' (lowercase) in
    # `format_line()`, we can't count 'percent' as an example of a
    # lowercase word.
    words = re.findall(r"[a-zA-Z]+", sentence)
    #
    words = filter(lambda w: w != 'percent', words)
    #
    # Check that there's a lowercase letter in a word
    if any(re.match(r"[a-z]", w) for w in words):
        return sentence

    # Because we've now found that it's uppercase, we'll go through and
    # see if we can change each word.
    #
    # If the original uppercase word is in the lexicon, we'll leave it
    # because it may be an acronym. Additionally, unrecognized words
    # will also be left as uppercase.
    #
    # We need to allow "'" because of contractions. Our minimum length
    # is to filter out acronyms. There is ONE single-letter word in
    # English that should remain lowercase: "a", so we'll deal with that
    # immediately after this substitution
    pattern = r"[A-Z']{2,}"
    #
    def sub_word(w):
        w = w.group(0)

        # There's a special case for contractions like "I'm" and "I've":
        # Because they're mixed case, we can't just write `w.lower()`,
        # so we'll specifically filter out contractions that start with
        # `I'`
        if w.startswith("I'"):
            lower = w[:2] + w[2:].lower()
            if w in lexicon or lower not in lexicon:
                return w

            return lower

        if w in lexicon or w.lower() not in lexicon:
            return w

        return w.lower()
    #
    sentence = re.sub(pattern, sub_word, sentence)
    # Now we'll deal with "a". We just need to make sure that it's not
    # part of an acronym
    sentence = re.sub(r"((?<=^)|(?<= ))A(?=[ ,;:?!]|\.$)", "a", sentence)

    # Make sure that the first word is capitalized
    sentence = re.sub(r"^[a-z]", lambda m: m[0].upper(), sentence)

    return sentence

def do_video(videoID):
    groups = read_groups(videoID)
    if groups is None:
        return

    # for g in groups:
    #     print(g.lines)

    groups = preprocess_groups(groups)

    sentences = to_sentences(groups)
    sentences = filter_sentences(sentences)
    sentences = [ensure_lowercase(s) for s in sentences]
    write_sentences(videoID, sentences)

# These lines are for testing purposes -- in order to test on a single
# video. Uncomment `do_video` and comment out everything following
# 'Main:' to test.
# do_video('1ZAPwfrtAFY')
# do_video('UB1cGaIW81I')
# do_video('069D0NmW39o')

# Main:
video_ids = vlist.video_ids()

#
progress_width = 30
#
keep = list(filter(lambda v: v not in garbage_subs, video_ids))
for i, videoID in enumerate(keep):
    # Make a progress bar
    # should look like this:
    # [====================>          ] 67%
    p = int(i / len(keep) * progress_width)
    percent = int(100 * i / len(keep))
    sys.stdout.write('\r[' + '='*p + '>' + ' '*(progress_width-p) + '] {}%'.format(percent))
    sys.stdout.flush()
    
    # print(videoID)
    do_video(videoID)

# print the progress bar as complete
print("\r[{}>] 100%".format('='*progress_width))