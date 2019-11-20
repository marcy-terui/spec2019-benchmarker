import copy
import json
import math
import os
import random
import uuid
import time

import boto3
import requests
from faker import Faker

fake = None
dynamo = None
locations = None

def _fake():
    global fake
    if fake is None:
        fake = Faker()
    return fake


def _get_dynamo():
    global dynamo
    if dynamo is None:
        dynamo = boto3.resource('dynamodb')
    return dynamo


def _get_locations():
    global locations
    if locations is None:
        locations = json.loads(open('location.json', 'r').read())
    return locations


def get_url(event, context):
    item = _get_dynamo().Table(
        os.environ['TEAM_TABLE']).get_item(
            Key={'id': event['execution']['teamId']}
        ).get('Item', {})
    if item.get('stop', False) is True:
        raise Exception('Stopped.')
    url = item.get('url')
    if url is None:
        raise Exception('URL is not exists')
    event['execution']['url'] = url
    return event


def generate(event, context):
    senario = []
    users = _generate_users(event['execution']['concurrency'])
    for i in range(event['execution']['concurrency']):
        friend_i = i + 1
        if i % 2 == 1:
            friend_i = i - 1

        senario.append({
            'url': event['execution']['url'],
            'self': users[i]['id'],
            'friend': users[friend_i]['id'],
            'actions':  _generate_actions()
        })
    event['users'] = users
    event['senario'] = senario
    return event


def _generate_users(count):
    return [{'id': str(uuid.uuid4()), 'name': _fake().name()} for i in range(count)]


def _generate_actions():
    actions = []
    actions.append(_generate_charge_action(5))
    for _ in range(random.randint(5, 10)):
        actions.append(_generate_random_action())
    return actions


def _generate_charge_action(base=1):
    return {'charge': random.randint(base, 10) * 1000}


def _generate_random_action():
    return {random.choice(['charge', 'use', 'transfer']): random.randint(1, 50) * 100}


def execute_actions(event, context):
    results = []
    for action in event['actions']:
        for action_type, amount in action.items():
            if action_type == 'charge':
                results.append(
                    _charge_action(event['url'], event['self'], amount))
            elif action_type == 'use':
                results.append(
                    _use_action(event['url'], event['self'], amount))
            elif action_type == 'transfer':
                results.append(
                    _transfer_action(event['url'], event['self'], event['friend'], amount))
    return results


def _charge_action(url, use_id, amount):
    transaction_id = str(uuid.uuid4())
    location_id = random.randint(0, 1999)
    response = requests.post(
        f'{url}/wallet/charge',
        json={
            'transactionId': transaction_id,
            'userId': use_id,
            'locationId': location_id,
            'chargeAmount': amount})
    
    result = {
        'transactionId': transaction_id,
        'action': 'charge',
        'status': 'success',
        'userId': use_id,
        'amount': amount,
        'locationId': location_id,
        'time': response.elapsed.total_seconds(),
        'message': f'Action: Charge, TransactionId: {transaction_id}, Message: '}
    if response.status_code == 202:
        result['status'] = 'success'
        result['message'] += 'Suceeded.'
    else:
        result['status'] = 'error'
        result['message'] += f'Invalid status code: {response.status_code}.'
    return result


def _use_action(url, use_id, amount):
    transaction_id = str(uuid.uuid4())
    location_id = random.randint(0, 1999)
    response = requests.post(
        f'{url}/wallet/use',
        json={
            'transactionId': transaction_id,
            'userId': use_id,
            'locationId': location_id,
            'useAmount': amount})
    result = {
        'transactionId': transaction_id,
        'action': 'use',
        'status': 'success',
        'userId': use_id,
        'amount': amount,
        'locationId': location_id,
        'time': response.elapsed.total_seconds(),
        'message': f'Action: Use, TransactionId: {transaction_id}, Message: '}
    if response.status_code == 202:
        result['status'] = 'success'
        result['message'] += 'Suceeded.'
    elif response.status_code == 400:
        result['status'] = 'fail'
        result['message'] += 'Failed by balance insufficient.'
    else:
        result['status'] = 'error'
        result['message'] += f'Invalid status code: {response.status_code}'
    return result


def _transfer_action(url, from_id, to_id, amount):
    transaction_id = str(uuid.uuid4())
    location_id = random.randint(0, 1999)
    response = requests.post(
        f'{url}/wallet/transfer',
        json={
            'transactionId': transaction_id,
            'fromUserId': from_id,
            'toUserId': to_id,
            'locationId': location_id,
            'transferAmount': amount})
    result = {
        'transactionId': transaction_id,
        'action': 'transfer',
        'status': 'success',
        'fromUserId': from_id,
        'toUserId': to_id,
        'amount': amount,
        'locationId': location_id,
        'time': response.elapsed.total_seconds(),
        'message': f'Action: Transfer, TransactionId: {transaction_id}, Message: '}
    if response.status_code == 202:
        result['status'] = 'success'
        result['message'] += 'Suceeded.'
    elif response.status_code == 400:
        result['status'] = 'fail'
        result['message'] += 'Failed by balance insufficient.'
    else:
        result['status'] = 'error'
        result['message'] += f'Invalid status code: {response.status_code}'
    return result


def recieve_notification(event, context):
    time.sleep(1)
    table = _get_dynamo().Table(os.environ['NOTIFICATION_TABLE'])
    table.put_item(Item=json.loads(event['body']))
    return {
        'statusCode': 200,
        'body': json.dumps({'result': 'ok'})}


def location(event, context):
    return {
        'statusCode': 200,
        'body': _get_locations()}


def build_result(event, context):
    return json.dumps({
        'results': event['results'],
        'teamId': event['execution']['teamId'],
        'url': event['execution']['url']})


def check_results(event, context):
    results_by_user = {}
    points = []
    for record in event['Records']:
        data = json.loads(record['body'])
        for result in data['results']:
            for r in result:
                for k in ['userId', 'fromUserId', 'toUserId']:
                    if k in r:
                        if r[k] not in results_by_user:
                            results_by_user[r[k]] = []
                        if r['status'] == 'success':
                            _calc_success_result(r, results_by_user[r[k]], points)
                        if r['status'] == 'fail':
                            _calc_fail_result(r, results_by_user[r[k]], points)
                        if r['status'] == 'error':
                            _calc_error_result(r, results_by_user[r[k]], points)
    for user, results in results_by_user.items():
        _check_summary(data['url'], user, results, points)
        _check_history(data['url'], user, results, points)
    _update_result(data['teamId'], points)


def _update_result(team, points):
    score = 0
    messages = []
    status = 'SUCCESS'
    for p in points:
        point = p['point']
        reason = p['reason']
        score += point
        messages.append(f'Point: {point}, {reason}')
        if point < 0:
            status = 'FAILURE'
    boto3.client('lambda').invoke(
        FunctionName=os.environ['SEND_RESULTS_FUNCTION'],
        InvocationType='Event',
        Payload=json.dumps({
            'score': score,
            'team': team,
            'status': status,
            'comment': "<br/>".join(messages)
        }).encode())


def _check_history(url, user, results, points):
    response = requests.get(f'{url}/users/{user}/history')
    ret = response.json()

    expected_history = []
    response_history = []
    error_exists = False

    if len(results) == 0:
        error_exists = True

    for r in results:
        if 'transactionId' in r:
            expected_history.append(r['transactionId'])
        if r['status'] == 'error':
            error_exists = True
    for r in ret:
        if 'transactionId' in r:
            response_history.append(r['transactionId'])

    mismatch_history = []
    for h in expected_history:
        if h not in response_history:
            mismatch_history.append(h)

    if error_exists:
        points.append({
            'point': 0,
            'reason': f'Action: history, There are some error in the scenario.'})
    elif len(mismatch_history) > 0:
        tmp = ', '.join(mismatch_history)
        points.append({
            'point': len(mismatch_history),
            'reason': f'Action: history, Mismatched Transaction IDs: {tmp}.'})
    else:
        elapsed_time = response.elapsed.total_seconds()
        points.append({
            'point': math.floor(5 / elapsed_time),
            'reason': f'Elapsed time: {elapsed_time}, Action: history, Suceeded.'})


def _check_summary(url, user, results, points):
    current = 0
    charge = 0
    use = 0
    error_exists = False
    locations = _get_locations()
    times_per_location = {}
    if len(results) == 0:
        error_exists = True
    for r in results:
        if r['status'] == 'success':
            if r['action'] == 'charge':
                current += r['amount']
                charge += r['amount']
            elif r['action'] == 'use':
                current -= r['amount']
                use += r['amount']
            elif r['action'] == 'transfer':
                if user == r['fromUserId']:
                    current -= r['amount']
                    use += r['amount']
                elif user == r['toUserId']:
                    current += r['amount']
                    charge += r['amount']
            l = locations[str(r['locationId'])]
            if l not in times_per_location:
                times_per_location[l] = 1
            else:
                times_per_location[l] += 1
        elif r['status'] == 'error':
            error_exists = True

    response = requests.get(f'{url}/users/{user}/summary')
    ret = response.json()
    ok = True
    messages = ['Action: summary']

    if ret.get('currentAmount') != current:
        ok = False
        tmp = ret.get('currentAmount')
        messages.append(
            f'"currentAmount" expected "{current}" but got "{tmp}"')
    if ret.get('totalChargeAmount') != charge:
        ok = False
        tmp = ret.get('totalChargeAmount')
        messages.append(
            f'"totalChargeAmount" expected "{charge}" but got "{tmp}"')
    if ret.get('totalUseAmount') != use:
        ok = False
        tmp = ret.get('totalUseAmount')
        messages.append(
            f'"useAmount" expected "{charge}" but got "{tmp}"')
    if ret.get('timesPerLocation') != times_per_location:
        ok = False
        tmp = ret.get('timesPerLocation')
        messages.append(
            f'"timesPerLocation" expected "{times_per_location}" but got "{tmp}"')
    
    if ok:
        if error_exists:
            points.append({
                'point': 0,
                'reason': f'Action: summary, There are some error in the scenario.'})
        else:
            elapsed_time = response.elapsed.total_seconds()
            points.append({
                'point': math.floor(5 / elapsed_time) ,
                'reason': f'Elapsed time: {elapsed_time}, Action: summary, Suceeded.'})
    else:
        points.append({
            'point': -5,
            'reason': ', '.join(messages)})


def _calc_success_result(result, results, points):
    results.append(result)
    notifications = _get_notifications(result['transactionId'])
    message = result['message']
    elapsed_time = result['time']
    if len(notifications) == 0:
        points.append({
            'point': -1,
            'reason': f'{message} But, the result is "not" notified.'})
    else:
        points.append({
            'point': len(notifications),
            'reason': f'Elapsed time: {elapsed_time}, {message}'})


def _calc_fail_result(result, results, points):
    points.append({
        'point': 0,
        'reason': result['message']})


def _calc_error_result(result, results, points):
    points.append({
        'point': -2,
        'reason': result['message']})


def _get_notifications(transaction_id):
    return _get_dynamo().Table(os.environ['NOTIFICATION_TABLE']).query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('transactionId').eq(transaction_id)
    ).get('Items', [])


def send_results(event, context):
    return _get_dynamo().Table(os.environ['TEAM_TABLE']).update_item(
        Key={'id': event['team']},
        AttributeUpdates={
            'score': {
                'Value': event['score'],
                'Action': 'ADD'
            },
            'result': {
                'Value': event['comment'],
                'Action': 'PUT'
            }
        }
    )
