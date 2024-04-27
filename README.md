# SimpleProxyManager
Python multithreaded proxy manager, focused on scrapes

This project lives at https://github.com/amagnasco/SimpleProxyManager. Feel free to submit an issue or improvements!
Releases: https://pypi.org/project/SimpleProxyManager/

Warning: if using on macOS, don't use this if also using os.fork() due to dependency urllib.request

For an example implementation, check out dev/example.py.

Major dependencies: requests, urllib3.

## Constructor inputs:
- threads: number of processing threads to use
- wait: minimum and maximum time to wait between requests, and HTTP timeout. All in seconds.
- headers: HTTP headers to use (user agent, accept, and accept-language)
- test: URI to use for health check, and minimum and maximum time to wait between each proxy healthcheck (in seconds)

## Public API:
- Setup:
    - load: inputs a path to a list of proxies, ingests and tests them.
- Monitoring:
    - healthcheck: processes the "all" queue into "ready" or "broken" queues
    - available: returns the list of available proxies
    - broken: returns the list of broken proxies
- Use:
    - validate: inputs a URI, and runs it through urllib's parse
    - req: inputs a URI, validates it, assigns a proxy, and runs get. Returns {success: True, data: Response}, or {success: False, error: Exception}.
    - get: inputs a proxy and URI, and retrieves it. For advanced usage like externally queued/threaded/async'd setups.

## Version History
This project uses semantic versioning. 
- ### to-do:
    - abstract proxy assigner method from req
    - improve usage docs
    - improve error handling
    - add test cases
    - improve HTTP status code handling
    - differentiate input proxy list by http/https
    - add a "reset queues to all" method
    - improve manual exit handling
- ### 0.2.0:
    - add i18n
    - consolidate load conf into one dict/json
    - improve input and type checking
    - handle HTTPErrors into general exceptions
    - improve exit condition when 0 proxies available
    - simplify class name and init for cleaner import
    - updated example
- ### 0.1.1:
	- added GitHub > PyPi publication workflow
- ### 0.1.0:
    - First release! Functional enough to share, but some logs might still be in Spanish while I sort out the i18n. 
