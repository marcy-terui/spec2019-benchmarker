S.P.E.C. 2019 Benchmarker
==========

# Description
The benchmarker of S.P.E.C. 2019.

The theme application is [here](https://github.com/marcy-terui/spec2019-theme).

The competition portal site (frontend) is [here](https://github.com/hassaku63/serverlessdays2019-spec-frontend).

# Overview

![Overview Image](https://user-images.githubusercontent.com/4560264/69319985-a4999880-0c83-11ea-9d1b-96dee04c21a4.png)


# Requirements
- Your AWS Account
- Python 3.7
- Node.js 10
- [Serverless Framework](https://serverless.com/)
- Serverless Framework Plugins
  - [serverless-step-functions](https://github.com/horike37/serverless-step-functions)
  - [serverless-pseudo-parameters](https://github.com/svdgraaf/serverless-pseudo-parameters)
  - [serverless-python-requirements](https://github.com/UnitedIncome/serverless-python-requirements)

# Deploy

```sh
export APPSYNC_URL=<your-frontend-appsync-url>
export APPSYNC_REGION=<your-frontend-appsync-region>
export APPSYNC_APIKEY=<your-frontend-appsync-apikey>
npm install
sls deploy
```

# How to use

## Add the new team

```sh
sls invoke -f add -d '{"teamId": "<your-team-name>", "url": "<your-api-base-url>"}'
```

## Delete the team

```sh
sls invoke -f delete -d '{"teamId": "<your-team-name>"}'
```

## Start benchmark

**※ "concurrency" must not be less than 2**

### All teams

```sh
sls invoke -f start -d '{"concurrency": 2}'
```

### Choose one of the teams

```sh
sls invoke -f start -d '{"teamId": "<your-team-name>", "concurrency": 2}'
```

## Stop benchmark

### All teams

```sh
sls invoke -f stop
```

### Choose one of the teams

```sh
sls invoke -f stop -d '{"teamId": "<your-team-name>"}'
```

Authors
-------

Created and maintained by Serverless Comunity JP
