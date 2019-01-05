"""
Housing - INOPERABLE

-Character Mixin
-Exit Obj
-Room Mixin
-Design Menu

20:38 <Cloud_Keeper> Griatch: Thenomain revealed all when it came to 'Places'
20:39 <Cloud_Keeper> I assumed you've read the logs, but for those who don't
(V) picture a fireplace in a room. Those sitting at the fireplace are having a
conversation but that conversation isn't passed to everyone in the room. Just
those sitting at the fireplace
20:40 <DiscordBot> <Tehom> Apparently it's a very standard mush feature - it
was something Apostate asked me to implement very early on. Places/tabletalk,
that is
20:40 <Griatch> It's known as many different names across the hobby, I've known
it as "locations" or "sublocations" before.
20:40 <Cloud_Keeper> So I was thinking an object with a "sit" command, that
when you sit it replaces your say and pose commands with a custom one.
20:41 <Griatch> Tehom: How did you go about your implementation? This is one of
those things we have discussed back and forth in here quite a lot back in the
day (not for some time now though)
20:42 <Griatch> Some consider using dicts in Attributes but I've also seen
people using coordinate systems inside the room or even to use
rooms-within-rooms.
20:47 <Cloud_Keeper> Thinking outloud. If the say command is on the fireplace,
you could save putting any attributes on the player because the cmd.object
would be the fireplace
20:47 <Griatch> I suppose one could add  to the extended_room contrib with that
kind of functionality. My main reason for not doing so was always that in MUDs,
locations/places can depend quite a bit on your game system - should you be
able to evesdrop etc? Is what you hear based on your skills somehow etc? But
maybe it could still be implemented in a somewhat more general form.
20:48 <Cloud_Keeper> I've spoken before (long before) about a subscription
system because I intended to have some very very chatty objects/npcs
20:48 <Cloud_Keeper> So you "watch tv" to see all the messages from the TV

20:50 <Cloud_Keeper> G: yeah, that was what I was leaning towards. Possibly
making everything a channel
20:50 <Griatch> Subclass Channel and have people subscribe to it only if they
are in the room with the TV using that Channel subsclass yes
20:51 <Griatch> Make sure to unsubscribe them when they leave the room
20:51 <Cloud_Keeper> That could work. And it would work similar to 'places'
20:52 <Cloud_Keeper> Vincent: Could be a fundemental rewrite between letting
everything have it's own channel or trying to combine channels and objects"
20:52 <Cloud_Keeper> The other option
20:52 <Cloud_Keeper> Is to have all these messages flying around
20:53 <Cloud_Keeper> And your typeclass only lets the messages of the types you
specify thorugh to the client

20:54 <Griatch> One could do this "filtering" in a variety of ways.
Subscriptions would be one way. I guess you could also tag all output messages
and before sending them to every possible receiver in the location, check
against whatever setting they have (such as if they want to see messages tagged
with "road_message")


21:17 <DiscordBot> <Tehom> Griatch: My implementation for Places was a
typeclass that has a cmdset for tabletalk, joining the place, and leaving it.
It doesn't replace or suppress any existing commands, since it seems common
that tabletalk basically becomes an impromptu private channel for a few people
during a large event, pretty much like people using whisper with multiple
targets. I do think it could be easily done as channels, or any number of other
21:17 <DiscordBot> implementations
21:18 <Cloud_Keeper> Tehom: So it just describes you to a channel ic with a
separate key to speak to it>
21:18 <Griatch> Tehom: Aha, so the tabletalk command literally sits on a table
in the room that people then use to communicate - that is, they need to write
'tabletalk <text>' to communicate to others around the table?
21:18 <Cloud_Keeper> subscribes*
21:19 <Cloud_Keeper> Hm. That does make it way simpler than replacing cmds
21:20 <DiscordBot> <Tehom> Griatch: Right. It's really no different than just a
multi-whisper, I just formatted it a little differently. It probably would have
made more sense to implement it as a channel typeclass, though
21:21 <Cloud_Keeper> Oh it's not a channel, a multi-whisper to a list of
characters that the table maintains?
21:22 <Griatch> you get alternative say/emote etc commands that only reroute
outputs to the others around the 'table'.
21:22 <DiscordBot> <Tehom> Cloud_Keeper: Yeah, it just sends a msg to each
person at the table, more or less the same way whisper does. I think a channel
typeclass would probably be a more elegant implementation though
21:24 <Griatch> Tehom, I think I like your take on tabletalk better. If one
wanted to make it more complex, the 'tabletalk' command could add a new cmdset
to you with new implementations of say/emote etc that redirects outputs only to
your location.
21:25 <DiscordBot> <Tehom> I kind of feel like what I might do eventually is
make a series of more specialized methods for sending messages to people, since
I'm doing way too much in the base msg() method. Like way too many conditional
checks where I should probably be calling something like
character.receive_combat_message() or character.receive_language_message(),
etc. I dunno, I just sorta recoil at having a super long and complicated msg()
method thats doing so
21:25 <DiscordBot> many different things

22:16 <Cloud_Keeper> vincent-lg: Turning the idea of misusing tags way up to
11. If we assume that everyone and object has a dbref tag. You subscribe to a
persons messages by having a tag (key=dbref, category="say"). We could: 1. send
messages to everyone (as we currently do) and have the at_msg_receive only
allow messages through you're subscribed to. OR 2. in the say command, check
who has your tag in your location and only send it to them
22:18 <Cloud_Keeper> Re: method 2. having the contents of a room have a tag of
that location might be quicker (database search for objects with both tags)
than relying on object.location. That might be a quick option but feels hacky
(not a necessarily a bad thing)
22:19 <Cloud_Keeper> Method 2 has less database reads
22:27 <Cloud_Keeper> At that point we really are turning people into channels
:P
22:30 <Cloud_Keeper> 'Spaces' will just have a command which sends speak on a
different tag (a different frequency)
"""
