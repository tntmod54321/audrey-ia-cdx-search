# audrey-ia-cdx-search  
 Dump all urls from the internet archive CDX api  

# Help  
```
usage: ia-cdx-search.py [-h] [--break-on-empty] [-p PROXY] [-r RETRIES] [-to TIMEOUT] query outfile user

positional arguments:
  query                 cdx query
  outfile               file to write rows to
  user                  username for using the cdx api

options:
  -h, --help            show this help message and exit
  --break-on-empty      exit if there are no more rows, don't use if you are using filter flags
  -p PROXY, --proxy PROXY
                        http proxy to use
  -r RETRIES, --retries RETRIES
                        how many times to retry failed requests
  -to TIMEOUT, --timeout TIMEOUT
                        request timeout delay, set to 0 for no timeout
```

# Example  
 `py ia-cdx-search.py "url=youtube.com&matchType=domain" youtube.com.cdx YOURUSERNAME --break-on-empty`  
