#include "stadium.h"

/* Shared wall coordinates: u runs along the wall; depth points out of the arena. */
static Vector3 wall_point(int wall, fixed u, fixed y, fixed depth, fixed width, fixed length) {
    switch (wall) {
    case 0: return (Vector3){u, y, -length-depth};
    case 1: return (Vector3){width+depth, y, u};
    case 2: return (Vector3){-u, y, length+depth};
    default: return (Vector3){-width-depth, y, -u};
    }
}

static int wall_visible(int wall, Vector3 camera, fixed width, fixed length) {
    switch (wall) {
    case 0: return camera.z >= -length;
    case 1: return camera.x <= width;
    case 2: return camera.z <= length;
    default: return camera.x >= -width;
    }
}

/* Cache shared net vertices/edges once: no cell clipping or topology work in play. */
typedef struct { short u,y; } NetPoint;
typedef struct { unsigned short a,b; } NetEdge;
typedef struct {
    NetPoint points[256]; NetEdge edges[384];
    int point_count,edge_count,half,top;
} Net;
/* Geometry is read once per vertex, so keep this cache out of fast-code/stack RAM. */
static Net nets[2] __attribute__((section(".ewram"), aligned(4)));

static int add_point(Net *net,int u,int y) {
    for(int i=0;i<net->point_count;i++)
        if(net->points[i].u==u && net->points[i].y==y) return i;
    if(net->point_count>=256) return -1;
    int i=net->point_count++;
    net->points[i]=(NetPoint){u,y}; return i;
}
static void prepare_net(Net *net,int half,int top) {
    if(net->half==half && net->top==top) return;
    net->half=half;net->top=top;net->point_count=net->edge_count=0;
    static const short hu[6]={64,32,-32,-64,-32,32};
    static const short hv[6]={0,56,56,0,-56,-56};
    for(int col=0,u=-half-64;u<=half+64;u+=96,++col)
        for(int y=-112+(col&1)*56;y<=top+112;y+=112)
            for(int edge=0;edge<3;edge++) {
                int u0=u+hu[edge],y0=y+hv[edge],u1=u+hu[edge+1],y1=y+hv[edge+1];
                for(int boundary=0;boundary<4;boundary++) {
                    int d0=boundary==0?u0+half:boundary==1?half-u0:boundary==2?y0:top-y0;
                    int d1=boundary==0?u1+half:boundary==1?half-u1:boundary==2?y1:top-y1;
                    if(d0<0 && d1<0) {y0=y1=-1;break;}
                    if((d0<0)!=(d1<0)) {
                        int nu=u0+(u1-u0)*d0/(d0-d1),ny=y0+(y1-y0)*d0/(d0-d1);
                        if(d0<0) {u0=nu;y0=ny;} else {u1=nu;y1=ny;}
                    }
                }
                if(y0<0 || y1<0 || net->edge_count>=384) continue;
                int a=add_point(net,u0,y0),b=add_point(net,u1,y1);
                if(a>=0 && b>=0) net->edges[net->edge_count++]=(NetEdge){a,b};
            }
}

void draw_stadium_crowd(Vector3 camera, fixed width, fixed length) {
    /* One terrace surface per wall; spectators interpolate along projected rows
       instead of individually transforming hundreds of world-space points. */
    for(int wall=0;wall<4;wall++) {
        if(!wall_visible(wall,camera,width,length)) continue;
        fixed half=(wall&1)?length:width;
        Vector3 v[4]={wall_point(wall,-half,12*256,24*256,width,length),
                      wall_point(wall,half,12*256,24*256,width,length),
                      wall_point(wall,half,78*256,99*256,width,length),
                      wall_point(wall,-half,78*256,99*256,width,length)};
        Face f[4]={0};
        const int indices[4][3]={{0,1,2},{0,2,3},{2,1,0},{3,2,0}};
        for(int i=0;i<4;i++) {f[i].v1=indices[i][0];f[i].v2=indices[i][1];f[i].v3=indices[i][2];f[i].base_color=STAND_DARK;}
        Mesh strip={"CROWD",4,4,v,f,0};
        draw_model_world(&strip,(Vector3){0,0,0},0,0,0,FP_ONE,-1,RENDER_FLAT);
        for(int row=0;row<3;row++) {
            int x0,y0,x1,y1;
            Vector3 a=wall_point(wall,-half,(24+row*22)*256,(36+row*25)*256,width,length);
            Vector3 b=wall_point(wall,half,(24+row*22)*256,(36+row*25)*256,width,length);
            if(!project_vertex_world(a,&x0,&y0) || !project_vertex_world(b,&x1,&y1)) continue;
            if(x0>x1) {int t=x0;x0=x1;x1=t;t=y0;y0=y1;y1=t;}
            if(x1<0 || x0>=240 || x0==x1) continue;
            draw_line(x0,y0+2,x1,y1+2,STAND_LIGHT);
            int start=x0<0?0:x0,end=x1>239?239:x1;
            for(int x=start+((row+wall)&3);x<=end;x+=6) {
                int y=y0+(y1-y0)*(x-x0)/(x1-x0);
                if(y<1 || y>=159) continue;
                int seed=(x/6+row*7+wall*3)&7;
                u8 c=seed<4?CROWD_BLUE:seed<6?CROWD_ORANGE:CROWD_NEUTRAL;
                draw_point(x,y,c);draw_point(x,y-1,c);
            }
        }
    }
}

void draw_stadium_hex_walls(Vector3 camera, fixed width, fixed length, fixed height) {
    prepare_net(&nets[0],width/256,height/256);
    prepare_net(&nets[1],length/256,height/256);
    for(int wall=0;wall<4;wall++) {
        if(!wall_visible(wall,camera,width,length)) continue;
        Net *net=&nets[wall&1];
        int sx[256],sy[256]; unsigned char visible[256];
        for(int i=0;i<net->point_count;i++) {
            Vector3 p=wall_point(wall,net->points[i].u*256,net->points[i].y*256,0,width,length);
            visible[i]=project_vertex_world(p,&sx[i],&sy[i]);
        }
        for(int i=0;i<net->edge_count;i++) {
            int a=net->edges[i].a,b=net->edges[i].b;
            if(visible[a] && visible[b]) {
                if((sx[a]<0 && sx[b]<0)||(sx[a]>=240 && sx[b]>=240)||
                   (sy[a]<0 && sy[b]<0)||(sy[a]>=160 && sy[b]>=160)) continue;
                draw_line(sx[a],sy[a],sx[b],sy[b],WALL_HEX);
            } else if(visible[a] || visible[b]) {
                draw_world_line(wall_point(wall,net->points[a].u*256,net->points[a].y*256,0,width,length),
                                wall_point(wall,net->points[b].u*256,net->points[b].y*256,0,width,length),WALL_HEX);
            }
        }
        draw_world_line(wall_point(wall,-net->half*256,0,0,width,length),
                        wall_point(wall,net->half*256,0,0,width,length),STAND_RAIL);
    }
}

/* Open goal mouth, inset net and reinforced posts. Line geometry keeps the
   structure transparent and avoids large filled panels and their overdraw. */
void draw_stadium_goal(fixed z, fixed w, fixed h, u8 color) {
    fixed depth = z < 0 ? -INT_TO_FP(35) : INT_TO_FP(35);
    fixed back = z + depth;
    Vector3 front[4]={{-w,0,z},{w,0,z},{w,h,z},{-w,h,z}};
    Vector3 rear[4]={{-w,0,back},{w,0,back},{w,h,back},{-w,h,back}};
    /* Sparse net: eight columns, three rows, plus roof and side tension lines. */
    for(int i=1;i<8;i++) {
        fixed x=-w+(2*w*i)/8;
        draw_world_line((Vector3){x,0,back},(Vector3){x,h,back},149);
        draw_world_line((Vector3){x,h,z},(Vector3){x,h,back},149);
    }
    for(int i=1;i<3;i++) {
        fixed y=h*i/3;
        draw_world_line((Vector3){-w,y,back},(Vector3){w,y,back},149);
        draw_world_line((Vector3){-w,y,z},(Vector3){-w,y,back},149);
        draw_world_line((Vector3){w,y,z},(Vector3){w,y,back},149);
    }
    for(int i=0;i<4;i++) {
        draw_world_line(rear[i],rear[(i+1)&3],color);
        draw_world_line(front[i],rear[i],color);
    }
    /* White inner lip and colored outer rail make the opening easy to read. */
    for(int i=1;i<4;i++) draw_world_line(front[i],front[(i+1)&3],130);
    fixed rail=INT_TO_FP(3);
    draw_world_line((Vector3){-w-rail,0,z},(Vector3){-w-rail,h+rail,z},color);
    draw_world_line((Vector3){w+rail,0,z},(Vector3){w+rail,h+rail,z},color);
    draw_world_line((Vector3){-w-rail,h+rail,z},(Vector3){w+rail,h+rail,z},color);
    draw_world_line(front[0],front[1],color);
}
