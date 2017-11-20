Olympus Photosync Server
========================

Automatically connect to and sync photos from Olympus WiFi enabled cameras.

In its present state, this is a Python script running on a RaspberryPi on top of Alpine Linux. The script:

1) Configures and runs ``wpa_supplicant``.

2) Waits for a connection to be established.

3) Runs `olympus-photosync`_ and syncs all new media to a directory.

4) If a TM1637 is connected to the RaspberryPi, it is used to show the sync progress.


Setup
-----

Work in progress.


License
-------

Released under the terms of the `Revised BSD License`_.


.. |pypi| image:: https://img.shields.io/pypi/v/olympus-photosync.svg?style=flat-square&label=latest%20stable%20version

.. _`Revised BSD License`: https://raw.github.com/gvalkov/olympus-photosync/master/LICENSE
.. _`olympus-photosync`:  https://github.com/mauriciojost/olympus-photosync
