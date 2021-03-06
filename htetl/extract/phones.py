import re
import luigi
import logging
import pandas as pd
import string
from htetl.tasks import loadpages
from htetl import util


logger = logging.getLogger('luigi-interface')
logger.setLevel(logging.DEBUG)

# TODO actually test and optimize the regex
LEADING_NUMBER = '(\+?[1]?)'
DIGIT='(\d|one|two|three|four|five|six|seven|eight|nine|zero)\s*'
SEPARATOR = '(\s*|\s*(-|.|dash|dot)\s*)'
TERMINATING_SEPARATOR = '(\s+|\s*(-|.|dash|dot)\s*)'
AREA_CODE = '\(?((%s){3})\)?' % DIGIT
FIRST_THREE = '\(?((%s){3})\)?' % DIGIT
LAST_FOUR = '\(?((%s){4})\)?' % DIGIT

# Regex variables for matching
NUMBER_REGEX = re.compile(''.join([
    '(',
    LEADING_NUMBER, SEPARATOR, AREA_CODE,
    SEPARATOR, FIRST_THREE, SEPARATOR, LAST_FOUR,
    ')']),
    re.IGNORECASE)

SEPARATOR_REGEX = re.compile(SEPARATOR)

LEADING_INDEX = 1
AREA_CODE_INDEX = 4
FIRST_THREE_INDEX = 9
LAST_FOUR_INDEX = 14


def normalize(match_group):
    def _norm(text):
        lower_text = text.lower()
        for d, w in enumerate(['zero', 'one', 'two', 'three', 'four',
                               'five', 'six', 'seven', 'eight', 'nine']):
            lower_text = str(d).join(lower_text.split(w))

        return SEPARATOR_REGEX.sub('', lower_text)

    norm_area_code = _norm(match_group[AREA_CODE_INDEX].strip())
    norm_first_three = _norm(match_group[FIRST_THREE_INDEX].strip())
    norm_last_four = _norm(match_group[LAST_FOUR_INDEX].strip())

    return '-'.join([norm_area_code, norm_first_three, norm_last_four])

class ParsePhones(luigi.Task):
    '''
        Parses phone numbers from raw page data & saves phone numbets / post IDs in CSV file
    '''
    outfile = 'data/page_emails.csv'

    def requires(self):
        return loadpages.RawPageData()

    def output(self):
        return luigi.LocalTarget(self.outfile)

    def run(self):
	in_path = self.input().path
        logger.info("Processing {}".format(in_path))
        df = pd.read_csv(in_path)
        phones = []
        # go over each html and grap phones
        for i, row in df.iterrows():
            match = NUMBER_REGEX.findall(row["content"])

            if match:
                for phone in match:
                    pnumber=normalize(phone)

                    phones.append([row["id"],pnumber])

        phonedf = pd.DataFrame(phones)
        with open(self.output().path, 'a') as f:
        # write posting id & phones to CSV
            phonedf.to_csv(f,index=False)
