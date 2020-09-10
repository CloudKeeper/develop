"""
Batchcode for Balamb Garden.

"""

from evennia import create_object
from typeclasses import rooms, exits, characters

###############################################################################
# INITIATE ROOMS
###############################################################################

# BASEMENT

basement = create_object(rooms.Room, key="Basement")
garden_master = create_object(rooms.Room, key="Garden Master's Office")

# FLOOR 1

# Entrance Rooms
front_gate = create_object(rooms.Room, key="Front Gate")
front_courtyard = create_object(rooms.Room, key="Front Courtyard")
reception = create_object(rooms.Room, key="Reception")
front_lobby = create_object(rooms.Room, key="Front Lobby")
lower_lobby = create_object(rooms.Room, key="Lower Lobby")
upper_lobby = create_object(rooms.Room, key="Upper Lobby")
lower_lobby = create_object(rooms.Room, key="Lower Lobby")
lower_lobby = create_object(rooms.Room, key="Lower Lobby")
lower_lobby = create_object(rooms.Room, key="Lower Lobby")

# Infirmary Rooms
infirmary_hallway = create_object(rooms.Room, key="Infirmary Hallway")
infirmary = create_object(rooms.Room, key="Infirmary")
infirmary_bed1 = create_object(rooms.Room, key="Infirmary Bed 1")
infirmary_bed2 = create_object(rooms.Room, key="Infirmary Bed 2")
infirmary_upper = create_object(rooms.Room, key="Infirmary Upper Courtyard")
infirmary_lower = create_object(rooms.Room, key="Infirmary Lower Courtyard")

# Quad
quad_upper = create_object(rooms.Room, key="Quad Upper Courtyard")
quad_lower = create_object(rooms.Room, key="Quad Lower Courtyard")
quad = create_object(rooms.Room, key="Quad")
quad_garden = create_object(rooms.Room, key="Quad Garden")

# Ballroom
ballroom_lobby = create_object(rooms.Room, key="Ballroom Lobby")
ballroom = create_object(rooms.Room, key="Ballroom")
balcony = create_object(rooms.Room, key="Balcony")

# Cafeteria
cafeteria_hallway = create_object(rooms.Room, key="Cafeteria Hallway")
cafeteria = create_object(rooms.Room, key="Cafeteria")
cafeteria_seating = create_object(rooms.Room, key="Cafeteria Seating")
cafeteria_courtyard = create_object(rooms.Room, key="Infirmary Courtyard")

# Dormitory
dormitory_hallway = create_object(rooms.Room, key="Dormitory Hallway")
common_room = create_object(rooms.Room, key="Common Room")

# Parking Rooms
parking_hallway = create_object(rooms.Room, key="Parking Hallway")
parking_lot = create_object(rooms.Room, key="Parking Lot")

# Training Room
training_hallway = create_object(rooms.Room, key="Training Centre Hallway")
training_centre = create_object(rooms.Room, key="Training Centre")
forest_track = create_object(rooms.Room, key="Forest Track")
boudler_path = create_object(rooms.Room, key="Boulder Path")
river_room = create_object(rooms.Room, key="River Room")
training_lookout = create_object(rooms.Room, key="Training Centre Lookout")

# Library Rooms
library_hallway = create_object(rooms.Room, key="Library Hallway")
library = create_object(rooms.Room, key="Library")
library_study = create_object(rooms.Room, key="Library Study")
library_upper = create_object(rooms.Room, key="Library Upper Courtyard")
library_lower = create_object(rooms.Room, key="Library Lower Courtyard")

# FLOOR 2
elevator_bridge = create_object(rooms.Room, key="Elevator Bridge")
hallway_a = create_object(rooms.Room, key="Hallway A")
class_a = create_object(rooms.Room, key="Classroom A")
class_a_back = create_object(rooms.Room, key="Back of Classroom A")
hallway_b = create_object(rooms.Room, key="Hallway B")
class_b = create_object(rooms.Room, key="Classroom B")
class_b_back = create_object(rooms.Room, key="Back of Classroom B")
hallway_c = create_object(rooms.Room, key="Hallway C")
class_c = create_object(rooms.Room, key="Classroom C")
class_c_back = create_object(rooms.Room, key="Back of Classroom C")
hallway_end = create_object(rooms.Room, key="End of the Hallway")
balcony2 = create_object(rooms.Room, key="Emergency Escape Balcony")

# FLOOR 3
headmaster_lobby = create_object(rooms.Room, key="Headmaster's Lobby")
headmaster_office = create_object(rooms.Room, key="Headmaster's Office")


# BASEMENT

basement = create_object(rooms.Room, key="Basement")
garden_master = create_object(rooms.Room, key="Garden Master's Office")


###############################################################################
# Detail Rooms
###############################################################################




# BASEMENT ROOMS

"""
Basement


"""
basement.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

basement.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

basement = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)


"""
Garden Master's Office


"""
garden_master.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

garden_master.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

garden_master = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)




# ENTRANCE ROOMS

"""
Front Gate


"""
front_gate.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

front_gate.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

front_gate_ex1 = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)


"""
Front Courtyard


"""
front_courtyard.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

front_courtyard.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

front_courtyard = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)

"""
Reception


"""
reception.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

reception.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

reception = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)

"""
Front Lobby


"""
front_lobby.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

front_lobby.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

front_lobby = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)

"""
Upper Lobby


"""
upper_lobby.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

upper_lobby.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

upper_lobby = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)



# INFIRMARY ROOMS

"""
Infirmary Hallway


"""
infirmary_hallway.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

infirmary_hallway.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

infirmary_hallway = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)

"""
Infirmary


"""
infirmary.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

infirmary.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

infirmary = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)

"""
Infirmary Bed 1


"""
infirmary_bed1.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

infirmary_bed1.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

infirmary_bed1 = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)

"""
Infirmary Bed 2


"""
infirmary_bed2.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

infirmary_bed2.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

infirmary_bed2 = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)

"""
Infirmary Upper Courtyard


"""
infirmary_upper.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

infirmary_upper.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

infirmary_upper = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)

"""
Infirmary Lower Courtyard


"""
infirmary_lower.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

infirmary_lower.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

infirmary_lower = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)


# QUAD ROOMS

"""
Quad Upper Courtyard


"""
quad_upper.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

quad_upper.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

quad_upper = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)

"""
Quad Lower Courtyard


"""
quad_lower.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

quad_lower.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

quad_lower = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)

"""
Quad


"""
quad.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

quad.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

quad = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)

"""
Quad Garden


"""
quad_garden.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

quad_garden.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

quad_garden = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)



# BALLROOM ROOMS

"""
Ballroom Lobby


"""
ballroom_lobby.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

ballroom_lobby.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

ballroom_lobby = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)

"""
Ballroom


"""
ballroom.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

ballroom.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

ballroom = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)

"""
Ballroom Balcony


"""
ballroom_balcony.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

ballroom_balcony.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

ballroom_balcony = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)



# CAFETERIA ROOMS

"""
Cafeteria Hallway


"""
cafeteria_hallway.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

cafeteria_hallway.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

cafeteria_hallway = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)

"""
Cafeteria


"""
cafeteria.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

cafeteria.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

cafeteria = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)

"""
Cafeteria Seating


"""
cafeteria_seating.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

cafeteria_seating.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

cafeteria_seating = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)

"""
Infirmary Courtyard


"""
cafeteria_courtyard.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

cafeteria_courtyard.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

cafeteria_courtyard = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)



# DORMITORY ROOMS


"""
Dormitory Hallway


"""
dormitory_hallway.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

dormitory_hallway.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

dormitory_hallway = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)

"""
Common Room


"""
common_room.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

common_room.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

common_room = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)




# PARKING ROOMS


"""
Parking Hallway


"""
parking_hallway.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

parking_hallway.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

parking_hallway = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)

"""
Parking Lot


"""
parking_lot.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

parking_lot.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

parking_lot = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)




# TRAINING ROOMS


"""
Training Centre Hallway


"""
training_hallway.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

training_hallway.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

training_hallway = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)

"""
Training Centre


"""
training_centre.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

training_centre.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

training_centre = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)

"""
Forest Track


"""
forest_track.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

forest_track.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

forest_track = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)

"""
Boulder Path


"""
boudler_path.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

boudler_path.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

boudler_path = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)

"""
River Room


"""
river_room.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

river_room.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

river_room = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)

"""
Training Centre Lookout


"""
training_lookout.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

training_lookout.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

training_lookout = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)





# LIBRARY ROOMS


"""
Library Hallway


"""
library_hallway.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

library_hallway.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

library_hallway = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)

"""
Library


"""
library.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

library.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

library = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)

"""
Library Study


"""
library_study.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

library_study.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

library_study = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)

"""
Library Upper Courtyard


"""
library_upper.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

library_upper.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

library_upper = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)

"""
Library Lower Courtyard


"""
library_lower.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

library_lower.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

library_lower = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)




# SECOND FLOOR ROOMS


"""
Elevator Bridge


Can look down to lobby room below.
Blue stripe leading to hallway
Blue tribal pattern runs along skirting boards.
"""
elevator_bridge.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

elevator_bridge.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

elevator_bridge = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)

"""
Classroom Hallway


"""
class_hallway.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

class_hallway.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

class_hallway = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)

"""
Classroom A


"""
class_a.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

class_a.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

class_a = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)

"""
Back of Classroom A


"""
class_a_back.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

class_a_back.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

class_a_back = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)

"""
Classroom B


"""
class_a.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

class_a.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

class_a = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)

"""
Back of Classroom B


"""
class_a_back.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

class_a_back.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

class_a_back = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)

"""
Classroom C


"""
class_a.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

class_a.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

class_a = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)

"""
Back of Classroom C


"""
class_a_back.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

class_a_back.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

class_a_back = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)

"""
Emergency Escape Balcony


"""
emergency_balcony.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

emergency_balcony.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

emergency_balcony = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)





# FLOOR 3 ROOMS

"""
Headmaster's Lobby

Receptionists desk and chair.
Frosted glass wall
Crest above Office door
Red carpet towards Office
Checkerboard grey and dark grey tile floor.
Ivory dome roof
"""
headmaster_lobby.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

headmaster_lobby.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

headmaster_lobby = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)

"""
Headmaster's Office

Headmaster throne
Polished concrete floor. Blue tribal pattern on floor.
red carpet leading to throne
tables along walls - Ivory bench, gold legs.
High candles on table.
Glass dome
ivory shades, gold posts.

"""
headmaster_office.db.desc = (
    "Test test test test test test test test test test test test test test test"
    )

headmaster_office.db.details[""] = (
    "Test test test test test test test test test test test test test test test"
    )

headmaster_office = create_object(exits.Exit, key="Enter",
                               aliases=["w"],
                               location=,
                               destination=)
