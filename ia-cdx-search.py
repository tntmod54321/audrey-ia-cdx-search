import argparse
import requests
import sqlite3
import sys
from urllib.parse import urlparse, parse_qs

def pprint(s):
    sys.stdout.write(s)
    sys.stdout.flush()

def joinqs(qsdict):
    return '&'.join([f'{k}={v}' for k, vals in qsdict.items() for v in vals])

def initdb(cur):
    cur.execute('''
        CREATE TABLE IF NOT EXISTS
        var_store (
            key TEXT PRIMARY KEY NOT NULL,
            val TEXT
        );
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS
        saved_pages (
            pagenum INT PRIMARY KEY NOT NULL,
            rowcount INT NOT NULL
        );
    ''')

cdxapi = 'https://web.archive.org/cdx/search/cdx'
def main():
    print(f'baseurl: {cdxapi}?{args.query}')
    useragent = f'audrey cdx query script, username: {args.user}'
    headers = {'user-agent': useragent}
    proxies={'http': args.proxy, 'https': args.proxy}
    
    # setup db
    conn = sqlite3.connect(f'{args.outfile}.sqlite')
    cur = conn.cursor()
    initdb(cur)
    
    # set cdx query
    cur.execute('INSERT INTO var_store (key, val) VALUES (?, ?) ON CONFLICT (key) DO NOTHING', ('cdx_query', args.query))
    conn.commit()
    cur.execute("SELECT val FROM var_store WHERE key = 'cdx_query'")
    if cur.fetchone()[0] != args.query:
        raise Exception('query changed! change or delete existing output files (sqlite+cdx)')
    
    # get page offset
    cur.execute("SELECT CAST(val AS INT) FROM var_store WHERE key = 'page_offset';")
    pagenum = (cur.fetchone() or (0,))[0]
    
    while True:
        # set query
        qs = parse_qs(args.query)
        qs.update({'output': ['json'], 'pageSize': ['50'], 'page': [str(pagenum)]}) # append these to end but still overwrite
        qs.update(parse_qs(args.query))
        url = f'{cdxapi}?{joinqs(qs)}'
        
        print(f'requesting url: {url}')
        pprint(f'page {pagenum}: ')
        for a in range(args.retries + 1):
            resp = requests.get(url, headers=headers, proxies=proxies, timeout=args.timeout or None)
            pprint(f'http {resp.status_code}, ')
            if resp.status_code in [504]:
                continue
            else:
                break
        
        if resp.status_code == 400:
            print('400 error, this probably means we have paginated all urls, exiting...')
            break
        elif not resp.status_code in [200]:
            cur.close()
            conn.close()
            raise Exception(f'unexpected status code {resp.status_code}')
        
        rowcount = resp.text.count("\n")
        if 'output=json' in url: # don't count json row header
            rowcount -= 1
        print(f'{rowcount} rows')
        
        if rowcount:
            print(f'lastrow: {resp.text.split("\n")[-1]}')
        
        # write data
        if rowcount:
            with open(args.outfile, 'a+', encoding='utf-8') as fh:
                fh.write(resp.text + '\n')
        
        # update db
        pagenum += 1
        cur.execute('INSERT INTO saved_pages (pagenum, rowcount) VALUES (?, ?)', (pagenum, rowcount))
        cur.execute('INSERT INTO var_store (key, val) VALUES (?, ?) ON CONFLICT (key) DO UPDATE SET val = EXCLUDED.val', ('page_offset', pagenum))
        conn.commit()
        
        if args.break_on_empty and not rowcount:
            print('empty page, it appears we have iterated all rows, exiting...')
            break
        
    cur.close()
    conn.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('query', help='cdx query') # ex: url=youtube.com&matchType=domain
    parser.add_argument('outfile', help='file to write rows to')
    parser.add_argument('user', help='username for using the cdx api')
    parser.add_argument('--break-on-empty', action='store_true', help='exit if there are no more rows, don\'t use if you are using filter flags')
    parser.add_argument('-p', '--proxy', default=None, help='http proxy to use') # my IP is still banned D:
    parser.add_argument('-r', '--retries', type=int, default=5, help='how many times to retry failed requests')
    parser.add_argument('-to', '--timeout', type=int, default=120, help='request timeout delay, set to 0 for no timeout')
    args = parser.parse_args()
    
    main()
