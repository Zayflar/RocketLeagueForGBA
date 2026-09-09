/**
 * @file models.h
 * @brief 3D Model definitions for the GBA 3D engine.
 */

#ifndef MODELS_H
#define MODELS_H

#include "engine3d.h"

/* --- Static Meshes --- */
extern Mesh cube_mesh;
extern Mesh pyramid_mesh;
extern Mesh spaceship_mesh;
#define CAR_MODEL_COUNT 3
extern const Mesh *const car_models[CAR_MODEL_COUNT];
extern Mesh rover_mesh;
extern Mesh car_mesh;
extern Mesh opp_car_mesh;
extern Mesh ball_mesh;
extern Mesh goal_mesh;

/* --- Procedural Meshes --- */
extern Mesh torus_mesh;
extern Mesh sphere_mesh;
extern Mesh cylinder_mesh;
extern Mesh puck_mesh;
extern Mesh walls_mesh;
extern Mesh stadium_arena_mesh;

/**
 * @brief Generate vertices and faces for torus and sphere meshes.
 */
void init_dynamic_models(void);


#endif /* MODELS_H */
