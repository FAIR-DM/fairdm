# Decisions: open any record from its portal ID

Rationale too long for the specification, and every ambiguity resolved while it was written.

## D1. The link sits at the portal's root, not under a prefix

A prefix such as `/id/` would keep the link out of every other page's way, at the cost of a
longer link and one more thing to explain. It buys nothing here. A portal ID has a fixed shape: one
of five letters followed by exactly 22 characters. None of the words a portal or an addon uses for
its pages has that shape, and the link is tried only after every page the portal declares, so a
declared page always wins. The maintainer asked for the root form.

## D2. A link is not remembered by the browser

The point of the link is that it survives a change to where pages live. A permanent redirect is
cached by browsers with no expiry, so a visitor who had followed a link once would keep going to
the old address after a move, which defeats the purpose. The link is answered as a temporary
redirect, and every visit asks the portal again.

## D3. Access is decided by the record's page

The link redirects to the record's page and leaves the access check to that page. A portal ID
cannot be guessed, so learning that an ID belongs to some record tells a visitor nothing they could
act on, and the page then answers exactly as it would to a visitor who had its address. Checking
access twice, in the link and in the page, would be a second copy of the rules to keep in step.

## D4. The API keeps its page addresses

The API's `url` field is documented as the address of the record's page, and clients follow it to
reach that page. Changing it would change a documented field for no client that has asked. A
machine that wants the permanent form can build it from the record's `uuid`, which the API already
returns.

## D5. Citations without an outside identifier use the link

A citation is the place a link is most likely to be kept for years, and today it carries the page
address whenever the record has no DOI or IGSN. A record with one goes on citing it, because an
identifier issued by an outside service outlives the portal itself, which the link cannot.

## D6. The address is called the record's permalink

The maintainer asked for the portal ID and the address on separate rows and for a name for the
address. "Permalink" is the word readers already know for a link that does not change. "Persistent
identifier" was not used: it would put the link beside DOIs and IGSNs, which outlive the portal, and
the permalink does not. "URI" belongs in metadata, not on a page people click.
