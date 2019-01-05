"""
Housing - INOPERABLE

-Character Mixin
-Exit Obj
-Room Mixin
-Design Menu

Hi Guys,

I've had an idea which will significantly side track me from my project but may
end up having some gains. Before I venture down it I want to make sure it's a
fully fleshed out goal. The idea is combining the functionality of channels
into all objects. Here are my use cases:

1. My game will have radio and TV objects which will emit messages every 10
seconds or so. I.e. The lyrics to songs in the case of the radio or the real
time events of a televised battle between players. Such messages will become
annoying to many players not interested in reading that text. Instead the
objects will intermittently emit a flavour message like "The TV drones on in
the background" much less frequently. The players interested in what it might
be saying would than enter a command "watch TV" or "listen radio". The object
will keep track of who's listening and send it's messages only to the listening
players.

2. I aim to give certain NPCs in my game an AI similar to that in Black and
White by Lionhead. As you can see the creature can be quite expressive.
Indicating tiredness by yawning, noticing and pointing out things, picking up
things. This again could become very annoying to many players, particularly if
many such NPCs were in the same location. Instead the objects would only
indicate major actions to the room but would send the majority of information
only to those players "watching" it.

3. This functionality may also be given to players, allowing for group
whispering and emoting in more populated areas.

4. There should be conversation places where characters gathered around a table
or fireplace can converse to everyone "sitting" at that spot without
necessarily passing that conversation to everyone in the room.

5. Needless to say, battles are quite message intensive. More so when there are
more than one battle occurring. Things like explosions might be emitted to the
room but the majority of messages only to those watching it.

All of these have similar functionality which makes me think they could be part
of the same system. As far as implementing this functionality:

1. My initial thought was to have an attribute list with a handler.

2. I realise that a lot of the functionality is shared with channels. My next
thought was for each object to have a connected modified channel.

3. My last thought, seeming channels are just a form of object, is to just
extend channels for all my objects such that the channels ARE the object.

I'd be interested to hear others point of view and other approaches.


18:00 S<solaxybat> That's a pretty neat concept, basically having private
channels that are object or location based, kind of like a subscription that
you can only get when in range.
18:01 S— solaxybat giggles at lalafell kissing. Prefers punting :D
18:02 C<Cloud_Keeper> It'd be very easy to do something like noise options.
Just choosing what level of objects the player automatically focuses on.
18:02 W<whitenoise> #4 is a good idea, but I don't like #3
18:02 W<whitenoise> #4 and #3 seem incompatible, almost. like, #4 would serve
well in an RP environment, but #3 would be more fitting to a hack n slash
environment where it's not meant to be immersive
18:03 S<solaxybat> I do like #5, so that while people 'in combat' get full
spam, people not in combat just occasionally get say, notification of a
scuffle, or a crit or botch or something. But... that's a level of detail that
makes my head spin.
18:03 C<Cloud_Keeper> Noted. It's more the implementation that I'm curious to
see others thoughts about.
18:04 S<solaxybat> That, and I need to trundle off to bed. I'll stay logged in
though :D
18:05 W<whitenoise> Cloud_Keeper: how to do that in Go would be very obvious,
and so I googled the equivalent and came up with these results which might be
interesting to experiment with. seems like you could test both methods
suggested in a matter of 30-40 minutes.
18:05 W<whitenoise>
http://stackoverflow.com/questions/19130986/python-equivalent-of-golangs-select-on-channels
18:06 C<Cloud_Keeper> I envisioned #3 and #4 fulfilling the same purpose where
#4 automatically fills in an audience rather than having to one by one have
people watch you.
18:06 W<whitenoise> but it's pretty interesting.
18:06 C<Cloud_Keeper> I'll have a look at the link.
18:07 W<whitenoise> you could also probably use Scripts to do it if you wanted
to stay totally within Evennia methods
18:07 W<whitenoise> in fact, you could definitely do that.
18:07 C<Cloud_Keeper> Most definitely. Either by keeping the list of players as
attributes on the script or the script generating the channel and acting as a
go between.
18:07 W<whitenoise> yep
18:08 W<whitenoise> and I am after all the person that is always trying to cram
as much functionality as possible into one system
18:08 W<whitenoise> so this is an intriguing problem
18:08 C<Cloud_Keeper> The one concern with merging objects and channels (or
expanding channels to be regular objects)  was a script based battle system
would have to use another implementation.
18:09 C<Cloud_Keeper> If I used a script as a go between then it's a matter of
slotting it in.

19:39 D<DiscordBot> <Phayte> Cloud_Keeper: Hopefully you get this message
tomorrow or whenever, but wanted to give you at least some feedback. The idea
actually sounds pretty cool. In some ways its almost like a walkie talkie
network. Its kinda neat to think you say a tv is broadcasting a pokemon match
from an arena. Tags were thrown around quite a bit too and if it was to keep
implementation simple, might be able to override like msg and check for a tag
on the
19:39 D<DiscordBot> level or detail people wanna hear.
19:40 D<DiscordBot> <Phayte> And you could breakdown detail level into sub
categories like combat, ambience, etc
19:41 D<DiscordBot> <Phayte> The mud I played on a long time ago allowed you to
switch level of detail of the room to like None, Brief, and Full so something
similar might work for filtering purposes.
20:04 C<Cloud_Keeper> That's actually a way I hadn't thought of. Working
backwards. Rather than sending messages to people on a list. Sending all
messages to everyone and filtering the messages

The key difference after all between channels and a system such as this is this
will still be limited to .location so hijacking .msg which already supports
messages based on .location is perhaps the most Evennia-centric approach.



People have discussed "making channels handle everything" before, I think this
is probably to use the Channel system for more than it was intended for. I
better like this approach of using objects themselves as the distributors.
The Tagging solution has the advantage of simplicity. Just have tags of "noise
level" on every character/AI receiver and have the sending object just check
those as for who should receive. This will likely work well as long as you are
only considering local room-wide effects with a small number of users. For
global sends it could get a bit heavy if the number of noise levels are few and
you have a lot of players or AI agents able to receive. Exactly how heavy is
probably something that would need to be benchmarked for your particular game.
Having each object store its subscriptions and only send to those has the
advantage of scaling independently of locality - there is no database query,
all that matters is that a receiver registered to be sent to; the sender just
needs to loop through the list of receiver references. Drawback is more
detailed book-keeping - if you store the subscriptions on the object all
receivers must also store a reference to that object so they can get to it to
unsubscribe! Unsubscribing can be an issue in general: If it's something like a
TV people chose to watch, either the room must be "in on it" and tell the TV to
remove people as they leave the room or the TV must filter its subscribers
receivers after if they are actually around. The latter is probably more
efficient since the TV can then weed out subscribers. It means people leaving
will have to re-watch when entering though.
A third option is to not let each object be a subscription service, but to
abstract this whole mechanism to a central handler. The SubscriptionHandler
allows sender objects to register themselves and lists which services they
offer. For example the TV would register with SUBHANDLER.add_sender(tvobj,
servicemap, auto_unsub_checker). Here the servicemap is a dictionary mapping
between service names and the relevant method on the tvobj typeclass, for
example "watch" or "unwatch". The auto_unsub_checker is a callable that the
handler runs on every receiver to see if they should be automatically removed
from the subscription (such as having left the room with the TV). Other objects
could now watch the TV with SUBHANDLER.subscribe(self, tvobj, "watch"). The
advantage of the external handler is mainly in the administration: You can
easily track all subscriptions in one place and list/fix things in one place.
The subscriber still need a reference to what it subscribes to in order to
unsubscribe with this suggestion (you could have the sender use a string hash
instead but the advantages of that are slim).


Resurrecting this thread to suggest one further method..

If we assume that everyone and object has a dbref tag. You subscribe to a
person’s messages by having a tag (key=dbref, category="say"). We could:



1. send messages to everyone (as we currently do) and have the at_msg_receive
only allow messages through you're subscribed to (you have their tag).

OR

2. in the say command, check who has your tag in your location and only send it
to them

Re: method 2. having the contents of a room have a tag of that location might
be quicker (database search for objects with both tags) than relying on
object.location. That might be a quick option but feels hacky (not necessarily
a bad thing). Method 2 has less database reads. At that point we really are
turning people into channels.



'Spaces' will just have a command which sends speak on a different tag (a
different frequency)



It seems like a reasonable size job, so any input or possible alternative
implementations would be appreciated



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
