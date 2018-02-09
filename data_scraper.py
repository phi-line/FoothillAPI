from urllib.request import urlopen
from os import makedirs
from os.path import abspath, join, exists
from collections import namedtuple, defaultdict
from json import dumps, JSONEncoder

# 3rd party
import requests
from bs4 import BeautifulSoup
from tinydb import TinyDB, Query

SCHEDULE = 'schedule.html'
TERM_CODE = '201841'
HEADERS = ('course', 'CRN', 'desc', 'status', 'days', 'time', 'start', 'end',
           'room', 'campus', 'units', 'instructor', 'seats', 'wait_seats', 'wait_cap')
DB_ROOT = 'db/'

def main():
    if not exists(DB_ROOT):
        makedirs(DB_ROOT, exist_ok=True)

    content = urlopen(f'file://{abspath(SCHEDULE)}') if exists(SCHEDULE) else mine(write=True)
    db = TinyDB(join(DB_ROOT, 'database.json'))

    # parse(content, db=db)

    try:
        # if len(db) > 0:
        #     entry = db.search(Query()['CHEM'].exists())
        #     # entry = db.table('CHEM')
        #     print(entry[0]['CHEM'])
        print(db.tables())
    except KeyError:
        pass


def mine(write=False):
    headers = {
        'Origin': 'https://banssb.fhda.edu',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'User-Agent': 'FoothillAPI',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'text/html, */*; q=0.01',
        'Referer': 'https://banssb.fhda.edu/PROD/fhda_opencourses.P_Application',
        'X-Requested-With': 'XMLHttpRequest',
        'Connection': 'keep-alive',
    }

    data = [('termcode', f'{TERM_CODE}'), ]

    res = requests.post('https://banssb.fhda.edu/PROD/fhda_opencourses.P_GetCourseList', headers=headers, data=data)
    res.raise_for_status()

    if write:
        with open(f'{SCHEDULE}', "wb") as file:
            for chunk in res.iter_content(chunk_size=512):
                if chunk:
                    file.write(chunk)

    return res.content


def parse(content, db=None):
    db.purge_tables()
    soup = BeautifulSoup(content, 'html5lib')

    tables = soup.find_all('table', {'class': 'TblCourses'})
    for t in tables:
        dept, dept_desc = t['dept'], t['dept-desc']

        rows = t.find_all('tr', {'class': 'CourseRow'})
        s = defaultdict(list)
        for r in rows:
            cols = r.find_all(lambda tag: tag.name == 'td' and not tag.get_text().isspace())

            if cols:
                for i, c in enumerate(cols):
                    a = c.find('a')
                    cols[i] = a.get_text() if a else cols[i].get_text()

                s[f'{cols[0]}'].append(namedtuple('data', HEADERS)(*cols))

        j = dict(s)
        db.table(f'{dept}').insert(j)


class Department():
    def __init__(self, dept, dept_desc):
        self.dept = dept
        self.dept_desc = dept_desc
        self.sections = list()

    def serialize(self):
        return {
            'dept': self.dept,
            'dept_desc': self.dept_desc,
            'sections': dumps(self.sections),
        }


if __name__ == "__main__":
    main()
