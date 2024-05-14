# SimpleProxyManager
Multithreaded proxy manager, focused on scrapes.

## Links: 
- [PyPi releases](https://pypi.org/project/SimpleProxyManager/)
- [GitHub releases](https://github.com/amagnasco/SimpleProxyManager/releases)
- [Example implementation](dev/example.py)
- [Development](https://github.com/amagnasco/SimpleProxyManager)
- [Issues and improvements](https://github.com/amagnasco/SimpleProxyManager/issues)
- [Security](SECURITY.md)

## Installation and usage:
- ```$ pip install simpleproxymanager```
- For an example implementation, check out [dev/example.py](dev/example.py)
- Set it up with a list of proxies, then use it to replace your usual HTTP requests.
- Has several configuration options (currently required, soon to be optional with defaults)

### Usage notes:
- Major dependencies: requests, urllib3.
- Warning: if using on macOS, don't use this if also using os.fork() due to dependency urllib.request

### Configuration:
- threads: number of processing threads to use
- wait: minimum and maximum time to wait between requests, and HTTP timeout. All in seconds.
- headers: HTTP headers to use (user agent, accept, and accept-language)
- test: URI to use for health check, and minimum and maximum time to wait between each proxy healthcheck (in seconds)

### Public API:
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
- [Example implementation](dev/example.py)

## Version History
This project uses semantic versioning. 
- ### 0.2.0:
    - upgraded concurrency model
    - fixed broken()
    - separated out proxy queues by schema
    - moved http headers from global to per-request
    - finished moving messages from ES to EN
    - added method for a pile of ordered requests
    - updated example
- ### 0.1.2a:
    - added SECURITY.md
    - updated docs
- ### 0.1.2:
    - handle HTTPErrors into general exceptions
    - simplify class name and init for cleaner import
    - updated example
- ### 0.1.1:
	- added GitHub > PyPi publication workflow
- ### 0.1.0:
    - First release! Functional enough to share, but some logs might still be in Spanish while I sort out the i18n. 
