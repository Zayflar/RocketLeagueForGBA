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
extern const Mesh *const car_match_models[CAR_MODEL_COUNT];
extern const Mesh *const car_far_models[CAR_MODEL_COUNT];
const Mesh *car_gameplay_mesh(int model, int distance_sq);
const Mesh *ball_gameplay_mesh(int distance_sq);
/* Keep the mesh bounds center fixed while pitching/rolling around a yawed car. */
Vector3 car_render_position(int model, Vector3 pos, int yaw, const int32_t rotation[9]);
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
