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

## Opinionated Mixpanel (and Customer.io) integration

The reason this package exists is to provide sane defaults when integrating with Mixpanel. Instead of chasing down event name typos and debugging why tracking does not work, you can focus on learning what is important to your users.

- You **never have typo-duplicated events** in Mixpanel, because every event name comes from a dataclass, never from a string that can be miss-typed by mistake.
- Same for properties. Like events, **properties are hardcoded** as dataclasses.
- All **"special" and "reserved" events and properties are already provided**, no need to chase them down in various Mixpanel docs.
- Your **app never stops working if Mixpanel is down**, but you still get errors in your logs so you know what is going on.
- You **never forget to call `flush()`** on the events buffer, since `pyramid_mixpanel` hooks into the request life-cycle and calls `flush()` at the end of the request processing.
- You **defer sending events until the entire request is processed successfully**, i.e. never send events like "User added a thing" if adding the thing to DB failed at a later stage in the request life-cycle.

NOTE: At the end of 2021, Mixpanel is [sunsetting their Email Messages](https://mixpanel.com/blog/why-were-sunsetting-messaging-and-experiments/) feature. Since we rely heavily on those at
[Niteo](https://niteo.co), we are adding [Customer.io](https://customer.io/) integration into this library, to replace Mixpanel's Email Messages. If you don't want to use Customer.io, nothing changes for you, just keep using `pyramid_mixpanel` as always. If you do want to use Customer.io, then
install this package as `pyramid_mixpanel[customerio]` and add the following registry settings. Then all `profile_set` and `track` calls will get automatically replicated to Customer.io. Other calls such as `profile_append` will only send to Mixpanel.

```ini
customerio.tracking.site_id: <secret>
customerio.tracking.api_key: <secret>
customerio.tracking.region: <eu OR us>
```


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

1. Include the following lines:

    ```python
    config.include("pyramid_mixpanel")
    ```

1. Tell mixpanel_mixpanel how you want to use it:


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

    # enable logging with structlog
    pyramid_heroku.structlog = true
    ```

For view code dealing with requests, a pre-configured `request.mixpanel`
is available.


## Design defense

The authors of `pyramid_openapi3` believe that while Mixpanel allows sending schema-less data, that can change as requirements for the project change, it is better to be precise about what "events" you send and what the properties of those events will be called. Same for "profiles". Here are the reasons that accumulated over 5 years of using Mixpanel at [Niteo](https://niteo.co):

a) There will be typos in event and property names. They will clutter your Mixpanel dashboard and slow you down.

b) There will be differently named events for similar actions sent from different parts of your codebase. Then in your Mixpanel dashboard you'll have `User Clicked Button` and `Button Clicked` events in you won't be sure which to use, and what's the difference between them.

c) Your events and properties will not be consistently named, because they will be sent from different parts of your codebase, by different authors. Your Mixpanel dashboard will feel somewhat "broken" because some events will be in past tense (`User Logged In`), some in all lowers caps (`generated invoice`), some with only the action verb (`click`) and so on.

All issues outlined above are alleviated using this package because all event & property names are defined as dataclasses, in a [single source of truth](https://github.com/niteoweb/pyramid_mixpanel/blob/eb47dcaa41e1f5de4134b066b90e9530d9318de2/pyramid_mixpanel/__init__.py#L29) manner. No typos are possible once the initial specification is done. You immediately recognize bad naming patterns because all event & property names are in a single file.

## Naming best practice

In order to have nice and consistent event and property names, the authors of this package suggest using the following guidelines when coming up with names:

* Use the `<item> <action>` format in past tense, i.e. `Button Clicked`, `Page Viewed`, `File Downloaded`.
* Use [Title Case](https://en.wikipedia.org/wiki/Letter_case#Title_Case).
* Frontend only sends two Mixpanel events: `Button/Link Clicked` and `Page Viewed`. We then construct custom events such as `Password Reset Button Clicked` or `Pricing Page Viewed` inside Mixpanel dashboard based on button name, URL, etc. Custom events can be modified retroactively, regular events cannot.
* Backend sends "action" events, when those actions finish successfully, such as `Site Deployed`, `PDF generated`, `Backup Completed`.
* More on https://segment.com/academy/collecting-data/naming-conventions-for-clean-data/.


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
