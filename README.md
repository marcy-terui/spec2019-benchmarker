S.P.E.C. 2019 Benchmarker
==========

# Description
The benchmarker of S.P.E.C. 2019.

The theme application is [here](https://github.com/marcy-terui/spec2019-theme).

The competition portal site (frontend) is [here](https://github.com/hassaku63/serverlessdays2019-spec-frontend).

# Requirements
- Your AWS Account
- Python 3.7
- Serverless Framework
- Serverless Framework Plugins
  - serverless-step-functions
  - serverless-pseudo-parameters
  - serverless-python-requirements

# Deploy

```
export APPSYNC_URL=<your-frontend-appsync-url>
export APPSYNC_REGION=<your-frontend-appsync-region>
export APPSYNC_APIKEY=<your-frontend-appsync-apikey>
sls deploy
```

# How to use

## Add the new team

```
sls invoke -f add -d '{"teamId": "<your-team-name>", "url": "<your-api-base-url>"}'
```

## Delete the team

```
sls invoke -f delete -d '{"teamId": "<your-team-name>"}'
```

## Start benchmark

**※ "concurrency" must not be less than 2**

### All teams

```
sls invoke -f start -d '{"concurrency": 2}'
```

### Choose one of the teams

```
sls invoke -f start -d '{"teamId": "<your-team-name>", "concurrency": 2}'
```

## Stop benchmark

### All teams

```
sls invoke -f stop
```

### Choose one of the teams

```
sls invoke -f stop -d '{"teamId": "<your-team-name>"}'
```

Authors
-------

Created and maintained by Serverless Comunity JP
