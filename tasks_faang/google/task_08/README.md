# Task 08: Pub/Sub Message Broker

**Time Limit: 60 minutes**

## Overview

You are given an in-memory publish/subscribe message broker. Publishers send messages
to topics, and subscribers receive messages from topics they're subscribed to.

## Current State

The broker supports topic creation, subscribing/unsubscribing, and publishing
messages. However, there are bugs in subscriber filtering, message ordering, and
concurrent unsubscribe handling.

## Bugs to Fix

There are **3 bugs** in the existing code:

1. **Subscriber receives its own published messages** — When a subscriber publishes
   a message to a topic it's subscribed to, it should NOT receive its own message,
   but currently it does.

2. **Message ordering not guaranteed in multi-topic subscription** — When a subscriber
   is subscribed to multiple topics, messages should be delivered in publish-order
   (FIFO), but they're not.

3. **Unsubscribe during message delivery crashes** — If a subscriber unsubscribes
   while messages are being delivered to other subscribers of the same topic,
   the delivery loop crashes with a RuntimeError (dictionary changed during iteration).

## Features to Implement

1. **Message Filtering** — Subscribers can provide a filter function that only
   delivers messages matching certain criteria.

2. **At-Least-Once Delivery** — Track message acknowledgment and redeliver
   unacknowledged messages after a timeout.

3. **Dead Letter Topic** — Messages that fail delivery N times are moved to
   a dead letter topic for manual inspection.

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```
