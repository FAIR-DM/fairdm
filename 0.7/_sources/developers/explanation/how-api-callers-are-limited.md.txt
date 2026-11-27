# How API callers are limited

This page explains how the API limits each caller, why there are two limits for each kind of caller, how callers are told apart, and where the counts live. It does not list the settings or their values, which are in [Settings](../reference/settings.md), and it does not say how to change them, which is in [How to change the API rate limits](../how-to/change-the-api-rate-limits.md).

## Why the API is limited

The API serves a portal's records to scripts. A script can ask far faster than a person can click, so a crawler or a loop with a bug can take a small server down. A limit per caller stops one caller from using the capacity of all the others. A caller over a limit is answered `429 Too Many Requests` with a `Retry-After` header that says how many seconds to wait, so a well-written script slows down instead of failing.

## Two limits for each caller

Each kind of caller has a limit over a minute and a limit over a day. They stop different things.

- The limit over a minute stops a burst, such as a loop that asks as fast as it can. It lets a caller recover quickly once it slows down.
- The limit over a day stops steady heavy use that no single minute would show.

One limit cannot do both. A daily figure large enough for honest use leaves a burst free to overload the server within minutes. A per-minute figure small enough to stop a burst, kept up all day, would be far too tight for a script that reads a large dataset steadily.

A caller who is signed in with a token or a session is allowed several times what an anonymous caller is. The portal knows who they are and can act on one account, which it cannot do for a stranger.

## Counted by address or by person

An anonymous caller is counted by the network address the request comes from. A signed-in caller is counted as the person, whatever address they use, so moving to another network does not reset the count. The signed-in limits ignore anonymous callers, so an anonymous caller is never held to the signed-in figure when that is the lower one.

## The proxy problem

Counting by address works only if the portal reads the right address. Most portals sit behind a reverse proxy or a load balancer, and then every request arrives from the proxy. The proxy passes the visitor's address along in the `X-Forwarded-For` header. A caller can write that header too.

If the portal trusts the whole header, a script that sends a different value in it on every request is counted as a new caller each time, and no limit ever stops it. If the portal ignores the header, every visitor is counted as the proxy, and one busy visitor uses up everyone's allowance.

The setting that resolves this is the number of proxies. With it, the portal takes the entry that the nearest proxy wrote, from the right-hand end of the header, which the caller cannot reach. FairDM sets no value, because the right number depends on the deployment and a wrong guess in either direction defeats the limits. A deployment check, `fairdm.W601`, warns until the number is set. Setting `0` is a valid answer for a portal with no proxy. The steps are in [How to count API callers behind a proxy](../how-to/count-api-callers-behind-a-proxy.md).

## Search boxes have limits of their own

The search boxes that choose a project, dataset, sample, measurement, person, organization, publication, tag or ROR entry send their requests to addresses of their own. Those addresses are open to anyone who can see the page. Each has the same two limits for each kind of caller, counted the same way.

They use scopes of their own, so typing in a search box does not use up anyone's API allowance. Typing comes in bursts that the API's figures were not set for, and a person filling in a form should not be locked out of the API they use in a script. A portal that replaced the dictionary of rates without these scopes keeps working search boxes, because each limit carries a starting value of its own. A caller over a limit is answered `429` with a `Retry-After` header and an empty list of results, before anything is searched. The record of the decision is [ADR 0039](../../adr/0039-autocomplete-addresses-are-limited-per-caller.md).

## Where the counts are kept

The counts live in the portal's default cache, which is Redis on a production portal. Every worker process of the portal shares them, so a limit holds however many processes serve the API.

If the cache cannot be reached, a request is not counted and none is refused for exceeding a limit. A cache that is down therefore turns the limits off rather than turning the API off. Keep the cache running. A development portal with no Redis holds its cache in memory, which belongs to one process, so the counts are not shared there.

## What the limits are not

The limits do not decide who may read or change a record. That is the job of the record's own access rules, described in [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md). They also do not tell one script from another behind the same address. Two scripts run from one office share the anonymous allowance, and the way out is a token, which counts each person separately.
