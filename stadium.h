#ifndef STADIUM_H
#define STADIUM_H
#include "engine3d.h"
void draw_stadium_crowd(Vector3 camera, fixed width, fixed length);
void draw_stadium_hex_walls(Vector3 camera, fixed width, fixed length, fixed height);
void draw_stadium_goal(fixed z, fixed half_width, fixed height, u8 color);
/* The quarter-circle joins the floor to each drivable wall. */
#define WALL_CURVE_RADIUS (32 * FP_SCALE)
Vector3 stadium_surface_vector(Vector3 v, int wall, int angle);
int stadium_surface_contact(Vector3 *pos, fixed radius, fixed tolerance,
    fixed width, fixed length, fixed goal_width, fixed goal_height,
    int *wall, int *angle, Vector3 *normal);
void draw_stadium_curves(Vector3 camera, fixed width, fixed length, fixed goal_width);
void draw_goal_effect(int x, int y, int age, int style, u8 color, int scale);
void draw_hockey_markings(fixed width, fixed length);
#endif
