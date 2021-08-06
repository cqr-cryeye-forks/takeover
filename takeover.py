#!/usr/bin/env python3
# takeover - subdomain takeover finder
# coded by M'hamed (@m4ll0k) Outaadi
import argparse
import concurrent
import concurrent.futures as thread
import json
import os
import re
import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

r = '\033[1;31m'
g = '\033[1;32m'
y = '\033[1;33m'
b = '\033[1;34m'
r_ = '\033[0;31m'
g_ = '\033[0;32m'
y_ = '\033[0;33m'
b_ = '\033[0;34m'
e = '\033[0m'

global _output
_output = []
services = {
    'AWS/S3': {'error': r'The specified bucket does not exist'},
    'BitBucket': {'error': r'Repository not found'},
    'Github': {'error': r'There isn\\\'t a Github Pages site here\.'},
    'Shopify': {'error': r'Sorry\, this shop is currently unavailable\.'},
    'Fastly': {'error': r'Fastly error\: unknown domain\:'},

    'Ghost': {'error': r'The thing you were looking for is no longer here\, or never was'},
    'Heroku': {'error': r'no-such-app.html|<title>no such app</title>|herokucdn.com/error-pages/no-such-app.html'},
    'Pantheon': {'error': r'The gods are wise, but do not know of the site which you seek.'},
    'Tumbler': {'error': r'Whatever you were looking for doesn\\\'t currently exist at this address.'},
    'Wordpress': {'error': r'Do you want to register'},

    'TeamWork': {'error': r'Oops - We didn\'t find your site.'},
    'Helpjuice': {'error': r'We could not find what you\'re looking for.'},
    'Helpscout': {'error': r'No settings were found for this company:'},
    'Cargo': {'error': r'<title>404 &mdash; File not found</title>'},
    'Uservoice': {'error': r'This UserVoice subdomain is currently available!'},
    'Surge': {'error': r'project not found'},
    'Intercom': {'error': r'This page is reserved for artistic dogs\.|Uh oh\. That page doesn\'t exist</h1>'},

    'Webflow': {
        'error': r'<p class=\"description\">The page you are looking for doesn\'t exist or has been moved.</p>'},
    'Kajabi': {'error': r'<h1>The page you were looking for doesn\'t exist.</h1>'},
    'Thinkific': {'error': r'You may have mistyped the address or the page may have moved.'},
    'Tave': {'error': r'<h1>Error 404: Page Not Found</h1>'},

    'Wishpond': {'error': r'<h1>https://www.wishpond.com/404?campaign=true'},
    'Aftership': {
        'error': r'Oops.</h2><p class=\"text-muted text-tight\">The page you\'re looking for doesn\'t exist.'},
    'Aha': {'error': r'There is no portal here \.\.\. sending you back to Aha!'},
    'Tictail': {'error': r'to target URL: <a href=\"https://tictail.com|Start selling on Tictail.'},
    'Brightcove': {'error': r'<p class=\"bc-gallery-error-code\">Error Code: 404</p>'},
    'Bigcartel': {'error': r'<h1>Oops! We couldn&#8217;t find that page.</h1>'},
    'ActiveCampaign': {'error': r'alt=\"LIGHTTPD - fly light.\"'},

    'Campaignmonitor': {'error': r'Double check the URL or <a href=\"mailto:help@createsend.com'},
    'Acquia': {
        'error': r'The site you are looking for could not be found.|If you are an Acquia Cloud customer and expect to see your site at this address'},
    'Proposify': {'error': r'If you need immediate assistance, please contact <a href=\"mailto:support@proposify.biz'},
    'Simplebooklet': {'error': r'We can\'t find this <a href=\"https://simplebooklet.com'},
    'GetResponse': {'error': r'With GetResponse Landing Pages, lead generation has never been easier'},
    'Vend': {'error': r'Looks like you\'ve traveled too far into cyberspace.'},
    'Jetbrains': {'error': r'is not a registered InCloud YouTrack.'},

    'Smartling': {'error': r'Domain is not configured'},
    'Pingdom': {'error': r'pingdom'},
    'Tilda': {'error': r'Domain has been assigned'},
    'Surveygizmo': {'error': r'data-html-name'},
    'Mashery': {'error': r'Unrecognized domain <strong>'},
    'Divio': {'error': r'Application not responding'},
    'feedpress': {'error': r'The feed has not been found.'},
    'readme': {'error': r'Project doesnt exist... yet!'},
    'statuspage': {'error': r'You are being <a href=\'https>'},
    'zendesk': {'error': r'Help Center Closed'},
    'worksites.net': {'error': r'Hello! Sorry, but the webs>'}
}


def plus(string):
    print('{0}[ + ]{1} {2}'.format(g, e, string))


def warn(string, _exit=False):
    print('{0}[ ! ]{1} {2}'.format(r, e, string))
    if exit:
        sys.exit()


def info(string):
    print('{0}[ i ]{1} {2}'.format(y, e, string))


def _info():
    return '{0}[ i ]{1} '.format(y, e)


def err(string):
    print(r'  |= [REGEX]: {0}{1}{2}'.format(y_, string, e))


def request(domain, proxy, timeout, user_agent):
    url = checkurl(domain)
    proxies = {
        'http': proxy,
        'https': proxy
    }
    redirect = True
    headers = {
        'User-Agent': user_agent
    }
    try:
        req = requests.get(
            url=url,
            headers=headers,
            verify=False,
            allow_redirects=redirect,
            timeout=int(timeout) if timeout else None,
            proxies=proxies
        )
        return req.status_code, req.content
    except requests.exceptions.RequestException as e:
        warn(f'Failed to establish a new connection for: {domain} Error: {e}', True)


def find(status, content, ok):
    for service in services:
        for values in services[service].items():
            if re.findall(str(values[1]), str(content), re.I) and int(status) in range(201 if ok is False else 200,
                                                                                       599):
                return str(service), str(values[1])


def banner():
    print("\n   /~\\")
    print("  C oo   ---------------")
    print(" _( ^)  |T|A|K|E|O|V|E|R|")
    print("/   ~\\  ----------------")
    print("#> by M'hamed (@m4ll0k) Outaadi")
    print("#> http://github.com/m4ll0k")
    print("-" * 40)


def checkpath(path):
    if os.path.exists(path):
        return path
    elif os.path.isdir(path):
        warn(f'"{path}" is directory!', True)
    elif os.path.exists(path) is False:
        warn(f'"{path}" not exists!', True)
    else:
        warn(f'Error in: "{path}"', True)


def readfile(path):
    info(f'Read wordlist.. "{path}"')
    return [x.strip() for x in open(checkpath(path), 'r')]


def checkurl(url):
    o = urllib.parse.urlsplit(url)
    if o.scheme not in ['http', 'https', '']:
        warn(f'Scheme "{o.scheme}" not supported!', True)
    if o.netloc == '':
        return 'http://' + o.path
    elif o.netloc:
        return o.scheme + '://' + o.netloc
    else:
        return 'http://' + o.netloc


def print_(string):
    sys.stdout.write('\033[1K')
    sys.stdout.write('\033[0G')
    sys.stdout.write(string)
    sys.stdout.flush()


def runner(args):
    with ThreadPoolExecutor(max_workers=args.threads) as thread_pool:
        if args.verbose:
            info(f'Set {args.threads} threads..')

        futures = [
            thread_pool.submit(requester, domain, args.proxy, args.timeout, args.user_agent, args.output, args.process,
                               args.verbose)
            for domain in args.domain
        ]

        for i, results in enumerate(concurrent.futures.as_completed(futures)):
            if results.exception():
                continue
            _output.append(results.result())


def requester(domain, proxy, timeout, user_agent, output, ok, v):
    if v:
        info('Domain: {}'.format(domain))
    code, html = request(domain, proxy, timeout, user_agent)
    service, error = find(code, html, ok)
    if service and error:
        if output:
            if v:
                plus('%s service found! Potential domain takeover found! - %s' % (service, domain))
            if v:
                err(error)
        return domain, service, error


def savejson(path, content, v):
    if v:
        info('Writing file..')

    a = [{
        'domain': domain,
        'service': service,
        'error': error
    }
        for domain, service, error in content
    ]
    with open(path, 'w+') as outjsonfile:
        json.dump(a, outjsonfile, indent=4)
    info(f'Saved at {path}..')


def savetxt(path, content, v):
    if v:
        info('Writing file..')
    br = '-' * 40
    bf = '=' * 40
    out = '' + br + '\n'
    for i in content:
        out += 'Domain\t: %s\n' % i[0]
        out += 'Service\t: %s\n' % i[1]
        out += 'Error\t: %s\n' % i[2]
        out += '' + bf + '\n'
    out += '' + br + '\n'
    with open(path, 'w+') as outtxtfile:
        outtxtfile.write(out)
        outtxtfile.close()
    info(f'Saved at {path}...')


def parse_args():
    parser = argparse.ArgumentParser()
    domain_group = parser.add_mutually_exclusive_group(required=True)
    domain_group.add_argument(
        '-d', '--domain',
        nargs='+',
        type=str,
        help='Set domain URL (e.g: www.test.com)'
    )
    parser.add_argument(
        '-th', '--threads',
        default=os.cpu_count() * 5,
        help='Set threads, default cpu count * 5'
    )
    domain_group.add_argument(
        '-i', '--input',
        help='Path to text file (*.txt) with targets'
    )
    parser.add_argument(
        '-p', '--proxy',
        help='Use a proxy to connect the target URL'
    )
    parser.add_argument(
        '-o', '--output',
        help='Use this settings to save a file, *.json or *.txt formats support'
    )
    parser.add_argument(
        '-t', '--timeout',
        default=20,
        help='Set a request timeout,default value is 20 seconds'
    )
    parser.add_argument(
        '-k', '--process',
        default=False,
        action='store_true',
        help='Process 200 http code, cause more false positive'
    )
    parser.add_argument(
        '-u', '--user-agent',
        dest='user_agent',
        default='Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:90.0) Gecko/20100101 Firefox/90.0',
        help='Set custom user agent (e.g: takeover-bot), default Mozilla/5.0'
    )
    parser.add_argument(
        '-v', '--verbose',
        default=False,
        action='store_true',
        help='Verbose, print more info'
    )
    return parser.parse_args()


def main():
    # --
    args = parse_args()
    banner()
    if args.verbose:
        info('Starting...')

    if args.input:
        args.domain = readfile(path=args.input)

    runner(args)
    if not args.output:
        return

    if args.output.endswith('.json'):
        savejson(args.output, _output, args.verbose)
    elif args.output.endswith('.txt'):
        savetxt(args.output, _output, args.verbose)
    else:
        warn(f"Output Error: {args.output.split('.')[-1]} extension not supported, only .txt or .json", True)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt as e:
        sys.exit(0)
