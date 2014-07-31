from ConfigParser import SafeConfigParser
import datetime
import json
import pprint
import pymongo
import requests
import sys
import operator
from collections import defaultdict
import pandas as pd
import numpy as np
import re

config = SafeConfigParser()
config.read('app.cfg')

#Your PagerDuty API key.  A read-only key will work for this.
PD_AUTH_TOKEN = config.get('pagerduty', 'auth_token')

#The Pagerduty API base url, make sure to include the subdomain
PD_BASE_URL = config.get('pagerduty', 'base_url')

# The Newrelic Insights API key
NRI_API_KEY = config.get('newrelic_insights', 'api_key')

# Newrelic Base URL
NRI_BASE_URL = config.get('newrelic_insights', 'base_url')
 
PD_HEADERS = {
    'Content-type': 'application/json',
	'Authorization': 'Token token={0}'.format(PD_AUTH_TOKEN),
}

NRI_HEADERS = {
    'Content-type': 'application/json',
    'X-Insert-Key': '{0}'.format(NRI_API_KEY),
}

def get_incidents(since=None, until=None, offset=0):

    params = {'since': since, 'until': until, 'offset': offset}
    response = requests.get(
      '{0}/incidents'.format(PD_BASE_URL),
      headers=PD_HEADERS,
      params=params
    )
    return response.json()

def get_incidents_count(since=None, until=None):
    params = {'since': since, 'until': until}
    count = requests.get(
		'{0}/incidents/count'.format(PD_BASE_URL),
		  headers=PD_HEADERS,
      params=params).json()['total']
    return int(count)

def get_all_incidents(since=None, until=None):
    '''
    Page thru incidents (100 incidents per page)
    '''
    total = get_incidents_count(since, until)
    current = 0
    data = []
    while current < total:
        response = get_incidents(since, until, current)
        data.append(response['incidents'])
        current += 100
    return data

def get_notes(incident_id):
    response = requests.get(
      '{0}/incidents/{1}/notes'.format(PD_BASE_URL, incident_id),
      headers=PD_HEADERS
    )
    return json.loads(response.content)

def publish_to_insights(data):
    print 'URL: {0}'.format(NRI_BASE_URL)
    print 'Headers: {0}'.format(NRI_HEADERS)
    print 'Data: {0}'.format(data)
    response = requests.post(
        '{0}'.format(NRI_BASE_URL),
        headers=NRI_HEADERS, data=data
    )
    return response

if __name__ == '__main__':
    now = datetime.datetime.now()
    delta = now - datetime.timedelta(days=1)

    events = []

    print 'Working on incident data'
    data = get_all_incidents(since=delta, until=now)

    # Data may return more than one page (100 incidents per page)
    for page in data:
      for incident in page:
        '''
        Note data is tied to incidents.  We are naively looping thru all incidents
        and pulling out notes if they are present.  Notes, by themselves, do not
        store the ID of the incident so we are including it in the stored document
        as incident_id (different from the id of the note itself).
        '''
        print 'Working on data for {0}'.format(incident['id'])
        incident_notes = get_notes(incident['id'])
        incident['notes'] = incident_notes

        if incident['resolved_by_user'] is None:
            resolved_by_user_name = 'N/A'
            resolved_by_user_email = 'N/A'
        else:
            resolved_by_user_name = incident['resolved_by_user']['name']
            resolved_by_user_email = incident['resolved_by_user']['email']
            
        event = {
          'eventType': 'PagerdutyIncident',
          'eventVersion': 2,
          'incident_number': int(incident['incident_number']),
          'incident_url': incident['html_url'],
          'incident_key': incident['incident_key'],
          'timestamp': incident['created_on'],
          'last_status_change_on': incident['last_status_change_on'],
          'created_on_hour': int(incident['created_on'].split('T')[1].split(':')[0]),
          'last_status_change_on_hour': int(incident['last_status_change_on'].split('T')[1].split(':')[0]),
          'service_name': incident['service']['name'],
          'service_id': incident['service']['id'],
          'escalation_policy_name': incident['escalation_policy']['name'],
          'escalation_policy_id': incident['escalation_policy']['id'],
          'trigger_type': incident['trigger_type'],
          'number_of_escalations': int(incident['number_of_escalations']),
          'resolved_by_user_name': resolved_by_user_name,
          'resolved_by_user_email': resolved_by_user_name
        }

        encoded_event = json.dumps(event, sort_keys=True, indent=4, separators=(',', ': '))
        print encoded_event
        response = publish_to_insights(encoded_event)
        print 'Response code: {0}'.format(response)
        print
