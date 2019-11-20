'use strict';

require('isomorphic-fetch');
const AUTH_TYPE = require('aws-appsync-auth-link/lib/auth-link').AUTH_TYPE;
const AWSAppSyncClient = require('aws-appsync').default;
const gql = require('graphql-tag');

const addBenchmarkResult = gql(`
  mutation addBenchmarkResult($input: AddBenchmarkResultInput!) {
    addBenchmarkResult(input: $input) {
      team
      status
      comment
      score
    }
  }`);

  const addBenchmarkResultHistory = gql(`
  mutation addBenchmarkResultHistory($input: AddBenchmarkResultHistoryInput!) {
    addBenchmarkResultHistory(input: $input) {
      team
      epochMilliSeconds
      status
      comment
      score
    }
  }`);

exports.sendResults = async (event) => {
  const client = new AWSAppSyncClient({
    url: process.env['APPSYNC_URL'],
    region: process.env['APPSYNC_REGION'],
    auth: {
      type: AUTH_TYPE.API_KEY,
      apiKey: process.env['APPSYNC_APIKEY']
    },
    disableOffline: true
  });

  try {
    console.log(JSON.stringify(
      await client.mutate({
        variables: {
          input: {
            team: event.team,
            status: event.status,
            comment: 'hello',
            score: event.score
          }
        },
        mutation: addBenchmarkResult
      })
    ));

    console.log(JSON.stringify(
      await client.mutate({
        variables: {
          input: {
            team: event.team,
            epochMilliSeconds: Date.now(),
            status: event.status,
            comment: event.comment,
            score: event.score
          }
        },
        mutation: addBenchmarkResultHistory
      })
    ));
    return {result: 'ok'}
  } catch (err) {
    console.log(JSON.stringify(err));
    return err;
  }
};
