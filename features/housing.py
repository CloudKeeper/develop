"""
Housing - INOPERABLE

-Character Mixin
-Exit Obj
-Room Mixin
-Design Menu

Trying to record some of the golden discussions had in the IRC channel.

One feature I am developing for my game is player housing. Each town will have
an apartment complex where you can buy an apartment and take a specific exit
which will automatically take you to your property or present you with the
options of properties you're allowed to visit at that location. We were
speaking about how best to facilitate that (Conversation has been edited for
readability and coherence):

<Cloud_Keeper> Rooms will have a tag for being an apartment at a certain
apartment building

<Cloud_Keeper> And a tag with characters.id with category of permission

<Cloud_Keeper> So if I want to know what rooms a character can go to, I'll
search for rooms with matching tags of the apartment building and the
characters.id


Vincent provided some amazing guidance for implementing the system:

<vincent-lg> say you store the owner of a room on the room itself as a tag

<vincent-lg> room.tags.add("own_{id}".format(id=owner.id), category="owner")

<vincent-lg> then you can get all owners in a single query without much trouble
because they share a category. You can check the ID quite easily.

<vincent-lg> but they can do a lot. In that case storing tags with
ownership/right to enter privileges on the object, with a specific category and
with the character ID as key is, in my opinion, a good approach. Easy for rooms
to list who can enter. Easy for character to see where they can go (that's just
a query with search_tag). It has some drawbacks but not a lot I believe.

<vincent-lg> I advised the "owner_{id" key, but actually str(char.id) is just
fine, why bother... it makes searching much easier, as long as you have a
consistent category (that's the key)

<Cloud_Keeper> Yes, I was thinking you could just have a tag for each
permission level

<vincent-lg> you store the owners/guests on the room (or whatever access level
you want). The room has access to them. When a character wants to know where
she can go, you'll just need to query tags with a set of common categories

<vincent-lg> I don't remember what manager is responsible for tags but you can
query it like you can ObjectDB

<vincent-lg> so you might end up with something like that: # with char being
the character allowed_rooms = ObjectDB.objects.get(db_tag=str(char.id))

<vincent-lg> ObjectDB.objects.get(db_tags__db_key=str(char.dbref))

<vincent-lg> (that will return every tag with key=the character ID, so you
might want to do it a bit better)

<vincent-lg>
ObjectDB.objects.filter(db_tags__db_key=str(char.id)).filter(
db_tags__db_categorh="whatevercategory")

<vincent-lg> to get all the tags of key char ID and of categories either 1 or 2
or 3, you'll need to get a Q() object and work from that.

<vincent-lg> 1. With categories as ["guest", "owner"] and char as a character
object: ObjectDB.objects.filter(db_tags__db_key=str(char.dbref),
db_tags__db_category__in=categories)

<vincent-lg> 2. Getting all rooms for char, no matter the tag:

<vincent-lg> ObjectDB.objects.filter(db_tags__db_key=str(char.dbref))

<vincent-lg> heree's my coordinate system:
https://github.com/evennia/evennia/wiki/Coordinates
<vincent-lg> it uses tags to track coordinates. Look at the get_rooms_around
method in particular that seems to be doing what you want
<vincent-lg> it's not abstract :D the tag system seems fairly close to what you
want. Griatch gave me the idea though I don't know if Im using them
correctly

Griatch provided some specific information of the tag and permission system:

<Griatch> Permissions *are* tags

<Griatch> It's just a special type of tag

<Griatch> tags have two levels of category, the tag_type and then the category.
The tags with tag_type=None are the normal tags, the ones with tag_type
"permissions" are permissions and those with tag_type="aliases" are aliases.

<Griatch> They have their own full query handlers

<Griatch> So you can query permissions like any other entity, they are just
referenced via their own convenient handler obj.permissions

<Griatch>
https://github.com/evennia/evennia/blob/master/evennia/typeclasses/managers.py#L153

<Griatch> The utils.search docstring is a little simplified compared to the
full one, it should likely be updated

<Griatch> Tags are much more efficient than Attributes not mainly because of
the pickling but because you will only need one Tag for all grid points and all
objects in a given column for example. With Attributes you need a new Attribute
object for every object using a given grid point.

<Griatch> This is why Tags should not be used for object-individual data like
id's. A single tag is only ever created once and is shared between all objects
it tags.

<Griatch> They are a way to group and organize objects. If you have one object
per tag ... why use a tag at all?


Hope there's some food for thought regarding other housing systems!





From what I gathered, Griatch is not favorable to using character IDs as tag
keys as I suggested.  To some extent, it would diminish (but not completely
remove, IMO) the point of tags being organizers, and one key leading to several
tags.


To be sure, storing character IDs as tag keys would allow to group, by
characters.  It means if you have a high range of characters as owners, you
will end up with a lot of tag keys and not a lot of tags for each row.  I can
understand why this is a problem.  But I don't know if there's a better way to
to do that.


So you could avoid tags and use attributes:


room.db.owner = character # assuming you have only one owner per room


They you could use search_attribute to retrieve th rooms some character owns.
But if you have several owners per room, things get complicated and tags seem
easier to use than attributes.


In this context there are two sides of the issue:


1. How to mark characters as owning the room?

2. How to retrieve all the rooms that a character owns in a single query
without iterating over all rooms?


Tags address both concerns.  Attributes don't seem to do the trick with #2.


To mediate and correct me if I'm wrong.






@vincent: Actually, I think I may have misunderstood what you wanted to do with
the tag-with-char-id concept. Whereas I do not generally like the concept of
storing dbrefs like this (anything that allows us to use objects directly is
better IMO), I can see the point of using tags for your two points above.

I suppose the alternative is to use Attributes on both ends:
room.db.owners = [Griatch, Vincent]
griatch.db.owned = [room]
vincent.db.owned = [room]
But this solution is still not as searchable as using a tag (as you point out).
.
Griatch

"""

"""
1.
Central Room
    Buy rooms with an NPC or command
    
Apartment rooms
    They have a tag to indicate connection to central room.

Characters
    They have a permissions tag with a category indicating level.

>Check if character has permissions
    Run check on player 

>Houses you own
    Check permission for owner
"""
