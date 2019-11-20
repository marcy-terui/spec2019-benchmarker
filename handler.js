'use strict';

const request = require('request-promise');
const AWS = require('aws-sdk');
const dynamodb = new AWS.DynamoDB.DocumentClient();
const stepfunctions = new AWS.StepFunctions();

module.exports.start = async event => {
  if (event.concurrency < 2) {
    return {result :'"concurrency" must not be less than 2.'}
  } else {
    let param = {TableName: process.env.TEAM_TABLE};
    if ('teamId' in event) {
      param.FilterExpression =  'id = :teamId';
      param.ExpressionAttributeValues =  {':teamId': event.teamId};
    }
    const data = await dynamodb.scan(param).promise();
    await Promise.all(data.Items.map(async (item) => {
      return await dynamodb.update({
        TableName: process.env.TEAM_TABLE,
        Key: {id: item.id},
        UpdateExpression: 'SET stop = :stop',
        ExpressionAttributeValues: {':stop': false}
      }).promise();
    }));
    await Promise.all(data.Items.map(async (item) => {
      return await stepfunctions.startExecution({
        stateMachineArn: process.env.SFN_ARN,
        input: JSON.stringify({
          execution: {
            teamId: item.id,
            concurrency: event.concurrency}
        }),
      }).promise();
    }));
    return {result :'ok'}
  }
};

module.exports.stop = async event => {
  let param = {TableName: process.env.TEAM_TABLE};
  if ('teamId' in event) {
    param.FilterExpression =  'id = :teamId';
    param.ExpressionAttributeValues =  {':teamId': event.teamId};
  }
  const data = await dynamodb.scan(param).promise();
  await Promise.all(data.Items.map(async (item) => {
    return await dynamodb.update({
      TableName: process.env.TEAM_TABLE,
      Key: {id: item.id},
      UpdateExpression: 'SET stop = :stop',
      ExpressionAttributeValues: {':stop': true}
    }).promise();
  }));
  return {result :'ok'}
};

module.exports.add = async event => {
  await dynamodb.put({
    TableName: process.env.TEAM_TABLE,
    Item: {
      id: event.teamId,
      url: event.url
    }
  }).promise();
  return {result :'ok'}
};

module.exports.delete = async event => {
  await dynamodb.delete({
    TableName: process.env.TEAM_TABLE,
    Key: {id: event.teamId}
  }).promise();
  return {result :'ok'}
};

module.exports.createUsers = async event => {
  await Promise.all(event.users.map(async (user) => {
    let options = {
      uri: `${event.execution.url}/users`,
      headers: {
        "Content-type": "application/json",
      },
      json: {
        "id": user.id,
        "name": user.name
      }
    };
    return await request.post(options).promise();
  }));
  return 'ok';
};
