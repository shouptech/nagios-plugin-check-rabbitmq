#!/usr/bin/env python
#
# check_rabbitmq.py

"""A program for remotely checking the health of RabbitMQ instance. Requires
   the management API available."""

from optparse import OptionParser
import urllib2
import base64

try:
    import json
except ImportError:
    # simplejson can be used with Python 2.4
    import simplejson as json

PLUGIN_VERSION = "0.1"

class RabbitAPIChecker(object):
    """Performs checks against the RabbitMQ API and returns the results"""

    # Nagios status codes (Nagios expects one of these to be returned)
    STATE_OK = 0
    STATE_WARNING = 1
    STATE_CRITICAL = 2
    STATE_UNKNOWN = 3

    def __init__(self, hostname, username, password, port=15672):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port

    def mem_alarm(self, args):
        """Calls the API and checks if a high memory alarm has been
           triggerred."""
        node = args[0]
        url = "http://%s:%s/api/nodes/%s" % (self.hostname, self.port, node)
        result = self.fetch_from_api(url)

        if 'mem_alarm' in result:
            if result['mem_alarm']:
                print "CRITICAL - Memory alarm triggered for %s" % node
                return self.STATE_CRITICAL
            else:
                print "OK - Memory alarm not triggered for %s" % node
                return self.STATE_OK
        else:
            print "UNKNOWN - mem_alarm not found in results from API"
            return self.STATE_UNKNOWN

    def fetch_from_api(self, url):
        """Calls the API and processes the JSON result."""
        request = urllib2.Request(url)
        base64string = base64.encodestring(
            '%s:%s' % (self.username, self.password)).replace('\n', '')
        request.add_header("Authorization", "Basic %s" % base64string)

        http_result = urllib2.urlopen(request)

        json_result = json.load(http_result)
        http_result.close()
        return json_result

def main():
    """Main entry point for program"""
    usage = "%prog [options] -H|--hostname HOST ACTION"
    parser = OptionParser(usage=usage,
                          version="%prog "+PLUGIN_VERSION)
    parser.add_option("-u", "--username", default="guest",
                      help="Username with monitoring access")
    parser.add_option("-p", "--password", default="guest",
                      help="Password for user with monitoring access")
    parser.add_option("-P", "--port", default=15672,
                      help="Port to run the API checks against")
    parser.add_option("-H", "--hostname",
                      help="Host to check")
    (options, args) = parser.parse_args()

    # Check for required arguments
    if len(args) < 1 or options.hostname == None:
        parser.print_usage()
        return RabbitAPIChecker.STATE_UNKNOWN

    checker = RabbitAPIChecker(options.hostname, options.username,
                               options.password, options.port)

    # Define actions available, will be found in args[0]
    actions = {'mem_alarm': checker.mem_alarm}

    try:
        if len(args) > 1:
            return actions[args[0]](args[1:])
        else:
            return actions[args[0]]()
    except KeyError:
        print "UNKNOWN - %s is not a valid action" % args[0]
        return RabbitAPIChecker.STATE_UNKNOWN
    except urllib2.HTTPError, exception:
        print "UNKNOWN - %s" % exception
        return RabbitAPIChecker.STATE_UNKNOWN
    except TypeError:
        print "UNKNOWN - %s requires one or more options" % args[0]
        return RabbitAPIChecker.STATE_UNKNOWN

if __name__ == "__main__":
    exit(main())
