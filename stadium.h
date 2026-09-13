#ifndef STADIUM_H
#define STADIUM_H
#include "engine3d.h"
void draw_stadium_crowd(Vector3 camera, fixed width, fixed length);
void draw_stadium_hex_walls(Vector3 camera, fixed width, fixed length, fixed height);
void draw_stadium_goal(fixed z, fixed half_width, fixed height, u8 color);
#endif
