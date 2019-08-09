## Changelog

0.3.0 (2019-08-09)
------------------

* Add guards that make sure parameters sent to MixpanelTrack are valid.
  [zupo]

* Don't flood logs with "mixpanel configured" messages.
  [zupo]

* Support for the `people_append` method.
  [suryasr007]

* Lots of cleanup of legacy assumptions:
  * `profile_sync` method was removed
  * request.user no longer required
  * MixpanelTrack init now accepts `distinct_id` instead of `user`
  * `state` ProfileProperty no longer required
  [zupo]


0.2.1 (2019-07-28)
------------------

* Not all consumers have a .flush() method.
  [zupo]


0.2.0 (2019-07-27)
------------------

* Rewrite based on 5 years of Mixpanel usage in production at Niteo.
  [@zupo, @vanclevstik, @dz0ny, @karantan, @am-on, @rokcarl]


0.1.14 - 0.1.65 (2012-2014)
---------------------------

* Legacy version developed by @hadrien.
