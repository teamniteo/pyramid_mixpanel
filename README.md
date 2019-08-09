## Integrate your [Pyramid](https://trypyramid.com) app with [Mixpanel](https://mixpanel.com/) to learn who your users are and how they are using your app.

<p align="center">
  <img height="200" src="https://github.com/niteoweb/pyramid_mixpanel/blob/master/header.jpg?raw=true" />
</p>

<p align="center">
  <a href="https://circleci.com/gh/niteoweb/pyramid_mixpanel">
    <img alt="CircleCI for pyramid_mixpanel (master branch)"
         src="https://circleci.com/gh/niteoweb/pyramid_mixpanel.svg?style=shield">
  </a>
  <img alt="Test coverage (master branch)"
       src="https://img.shields.io/badge/tests_coverage-100%25-brightgreen.svg">
  <img alt="Test coverage (master branch)"
       src="https://img.shields.io/badge/types_coverage-100%25-brightgreen.svg">
  <a href="https://pypi.org/project/pyramid_mixpanel/">
    <img alt="latest version of pyramid_mixpanel on PyPI"
         src="https://img.shields.io/pypi/v/pyramid_mixpanel.svg">
  </a>
  <a href="https://pypi.org/project/pyramid_mixpanel/">
    <img alt="Supported Python versions"
         src="https://img.shields.io/pypi/pyversions/pyramid_mixpanel.svg">
  </a>
  <a href="https://github.com/niteoweb/pyramid_mixpanel/blob/master/LICENSE">
    <img alt="License: MIT"
         src="https://img.shields.io/badge/License-MIT-yellow.svg">
  </a>
  <a href="https://github.com/niteoweb/pyramid_mixpanel/graphs/contributors">
    <img alt="Built by these great folks!"
         src="https://img.shields.io/github/contributors/niteoweb/pyramid_mixpanel.svg">
  </a>
  <a href="https://webchat.freenode.net/?channels=pyramid">
    <img alt="Talk to us in #pyramid on Freenode IRC"
         src="https://img.shields.io/badge/irc-freenode-blue.svg">
  </a>
</p>

## Opinionated Mixpanel integration

The reason this package exists is to provide sane defaults when integrating with Mixpanel. Instead of chasing down event name typos and debugging why tracking does not work, you can focus on learning what is important to your users.

- You **never have typo-duplicated events** in Mixpanel, because every event name comes from a dataclass, never from a string that can be miss-typed by mistake.
- Same for properties. Like events, **properties are hardcoded** as dataclasses.
- All **"special" and "reserved" events and properties are already provided**, no need to chase them down in various Mixpanel docs.
- Your **app never stops working if Mixpanel is down**, but you still get errors in your logs so you know what is going on.
- You **never forget to call `flush()`** on the events buffer, since `pyramid_mixpanel` hooks into the request life-cycle and calls `flush()` at the end of the request processing.
- You **defer sending events until the entire request is processed successfully**, i.e. never send events like "User added a thing" if adding the thing to DB failed at a later stage in the request life-cycle.


## Features

- Builds on top of https://mixpanel.github.io/mixpanel-python/.
- Provides a handy `request.mixpanel.*` helper for sending events and setting profile properties.
- Makes sure to call `.flush()` at the end of request life-cycle.
- Provides dataclasses for events and properties, to avoid typos.
- You can roll your own [`Consumer`](https://mixpanel.github.io/mixpanel-python/#built-in-consumers), for example one that schedules a background task to send events, to increase request processing speed, since HTTP requests to Mixpanel are offloaded to a background task.
- Provides a MixpanelQuery helper to use [JQL](https://mixpanel.com/jql/) to query Mixpanel for data. Some common queries like one for getting profiles by email are included.
- In local development and unit testing, all messages are stored in `request.mixpanel.api._consumer.mocked_messages` which makes writing integration tests a breeze.
- Automatically sets Mixpanel tracking `distinct_id` if `request.user` exists. Otherwise, you need to set it manually with `request.mixpanel.distinct_id = 'foo'`.


## Getting started

1. Declare `pyramid_mixpanel` as a dependency in your Pyramid project.

2. Include the following lines:

```python
config.include("pyramid_mixpanel")
```

3. Tell mixpanel_mixpanel how you want to use it:


```ini
# for local development and unit testing
# events will be stored in request.mixpanel.api._consumer.mocked_messages
mixpanel.token = false

# minimal configuration
mixpanel.token = <TOKEN>

# enable support for querying Mixpanel data
mixpanel.api_secret = <SECRET>

# custom events and properties
mixpanel.events = myapp.mixpanel.Events
mixpanel.event_properties = myapp.mixpanel.EventProperties
mixpanel.profile_properties = myapp.mixpanel.ProfileProperties

# defer sending of Mixpanel messages to a background task queue
mixpanel.consumer = myapp.mixpanel.QueuedConsumer
```

For view code dealing with requests, a pre-configured `request.mixpanel`
is available.


## Design defense

TODO:

## Running tests

You need to have [pipenv](https://pipenv.readthedocs.io/) and Python 3.7 installed on your machine. Then you can run:

    $ make tests

## Related packages

These packages are in the same problem-space:

- [old release of pyramid_mixpanel](https://pypi.org/project/pyramid_mixpanel/0.1.65/) by @hadrien had some neat ideas that this project built upon, even though it is a complete rewrite;
- the official [mixpanel-python](https://mixpanel.github.io/mixpanel-python/) is a lower-level library that this project depends on;
- mostly deprecated [Mixpanel-api](https://github.com/mixpanel/mixpanel_api) for querying data, superseded by [JQL](https://mixpanel.com/jql/);
- [mixpanel-jql](https://github.com/ownaginatious/mixpanel-jql) provides a Pythonic interface to writing JQL queries.


## Use in the wild

A couple of projects that use pyramid_mixpanel in production:

- [WooCart](https://woocart.com) - Managed WooCommerce service.
- [EasyBlogNetworks](https://easyblognetworks.com) - PBN hosting and autopilot maintenance.
- [Kafkai](https://kafkai.com) - AI generated content.
- [Docsy](https://docsy.org/) - Faceted search for private projects and teams.


# TODO:

* [ ] study https://pypi.org/project/pyramid_mixpanel/0.1.65/
* [ ] specify assumptions: request has a .user object that has .distinct_id
* [ ] stuctlog should be optional
* [x] study https://github.com/mixpanel/mixpanel-python/blob/master/demo/subprocess_consumer.py
* [x] CircleCI
* [x] 100% test coverage
* [x] 100% types coverage
* [x] custom Enums
* [ ] configure background task to be scheduled
* [ ] nicer error if dotted names are invalid
* [ ] nicer error if user is not set
* [x] flush BufferedConsumer at the end of request
* [x] add all Mixpanel special/reserved properties (those that make sense)
