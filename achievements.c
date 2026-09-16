#include "achievements.h"
/* Emulator save-type detection; the hardware uses byte-wide SRAM accesses. */
const char achievement_save_type[] __attribute__((used))="SRAM_V113";
const char *const achievement_names[ACH_COUNT]={"FIRST GOAL","STRIKER","WINNER","ICE BREAKER","WALL RIDER","GRADUATE","GOAL GETTER","SHARPSHOOTER","CENTURION","ON A ROLL","CHAMPION","LEGEND","ICE STRIKER","ICE LEGEND","WALL RUNNER","WALL MASTER","WALL LEGEND","DEBUT","REGULAR","VETERAN","SOCCER STAR","HOCKEY STAR","LINK RIVAL","CLEAN SHEET"};
const char *const achievement_descriptions[ACH_COUNT]={"SCORE 1 MATCH GOAL","SCORE 10 MATCH GOALS","WIN A FULL MATCH","SCORE 1 HOCKEY GOAL","WALL DRIVE: 3 SECONDS","FINISH ALL 6 LESSONS","SCORE 25 MATCH GOALS","SCORE 50 MATCH GOALS","SCORE 100 MATCH GOALS","WIN 5 MATCHES","WIN 10 MATCHES","WIN 25 MATCHES","SCORE 10 HOCKEY GOALS","SCORE 25 HOCKEY GOALS","WALL DRIVE: 15 SECONDS","WALL DRIVE: 30 SECONDS","WALL DRIVE: 60 SECONDS","FINISH 1 MATCH","FINISH 10 MATCHES","FINISH 50 MATCHES","WIN A SOCCER MATCH","WIN A HOCKEY MATCH","WIN A LINK MATCH","WIN WITHOUT CONCEDING"};
const uint16_t achievement_targets[ACH_COUNT]={1,10,1,1,180,1,25,50,100,5,10,25,10,25,900,1800,3600,1,10,50,1,1,1,1};
uint16_t achievement_progress[ACH_COUNT];
static volatile unsigned char *save;
static uint32_t generation,pending;
static int slot;
static uint32_t read32(const unsigned char *p) {
    return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;
}
static void write32(unsigned char *p,uint32_t n) {for(int i=0;i<4;i++)p[i]=(unsigned char)(n>>(i*8));}
static uint32_t checksum(const unsigned char *p,int length) {
    uint32_t h=2166136261u;
    for(int i=0;i<length;i++)h=(h^p[i])*16777619u;
    return h;
}
static int valid(const unsigned char *p,int legacy) {
    int count=legacy?6:ACH_COUNT,offset=8+count*2;
    if(p[legacy?31:63]!=0xa5 || read32(p)!=(legacy?0x31484341u:0x32484341u) ||
       read32(p+offset)!=checksum(p,offset))return 0;
    for(int i=0;i<count;i++)if((p[8+i*2]|p[9+i*2]<<8)>achievement_targets[i])return 0;
    return 1;
}
static void persist(void) {
    if(!save)return;
    unsigned char p[64]={0};write32(p,0x32484341);write32(p+4,++generation);
    for(int i=0;i<ACH_COUNT;i++) {p[8+i*2]=achievement_progress[i];p[9+i*2]=achievement_progress[i]>>8;}
    write32(p+56,checksum(p,56));slot^=1;
    int base=64+slot*64; /* Preserve the original six-achievement saves. */
    save[base+63]=0;
    for(int i=0;i<63;i++)save[base+i]=p[i];
    save[base+63]=0xa5;
}
void achievements_init(volatile unsigned char *storage) {
    save=storage;generation=pending=0;slot=1;
    for(int i=0;i<ACH_COUNT;i++)achievement_progress[i]=0;
    if(!save)return;
    int found=0;
    for(int legacy=0;legacy<=1;legacy++) {
        int size=legacy?32:64,offset=legacy?0:64;
        for(int s=0;s<2;s++) {
            unsigned char p[64]={0};for(int i=0;i<size;i++)p[i]=save[offset+s*size+i];
            if(valid(p,legacy) && (!found || (int32_t)(read32(p+4)-generation)>0)) {
                found=1;generation=read32(p+4);slot=s;
                for(int i=0;i<(legacy?6:ACH_COUNT);i++)achievement_progress[i]=p[8+i*2]|p[9+i*2]<<8;
            }
        }
        if(found) {
            if(legacy) {
                for(int i=ACH_GOALS_25;i<=ACH_GOALS_100;i++)achievement_progress[i]=achievement_progress[ACH_TEN_GOALS];
                for(int i=ACH_WINS_5;i<=ACH_WINS_25;i++)achievement_progress[i]=achievement_progress[ACH_WIN];
                for(int i=ACH_HOCKEY_10;i<=ACH_HOCKEY_25;i++)achievement_progress[i]=achievement_progress[ACH_HOCKEY];
                for(int i=ACH_WALL_15;i<=ACH_WALL_60;i++)achievement_progress[i]=achievement_progress[ACH_WALL];
                slot=1;persist();
            }
            break;
        }
    }
}
static int add_one(int id,unsigned amount) {
    unsigned before=achievement_progress[id],remaining=achievement_targets[id]-before;
    if(!remaining)return 0;
    achievement_progress[id]+=amount<remaining?amount:remaining;
    if(achievement_progress[id]==achievement_targets[id])pending|=1u<<id;
    return before!=achievement_progress[id];
}
void achievement_add(int id,unsigned amount) {
    if(id<0 || id>=ACH_COUNT || !amount)return;
    int changed=add_one(id,amount),first=-1,last=-1;
    if(id==ACH_TEN_GOALS){first=ACH_GOALS_25;last=ACH_GOALS_100;}
    if(id==ACH_WIN){first=ACH_WINS_5;last=ACH_WINS_25;}
    if(id==ACH_HOCKEY){first=ACH_HOCKEY_10;last=ACH_HOCKEY_25;}
    if(id==ACH_WALL){first=ACH_WALL_15;last=ACH_WALL_60;}
    if(id==ACH_MATCH){first=ACH_MATCHES_10;last=ACH_MATCHES_50;}
    unsigned wall_before=achievement_progress[ACH_WALL_60];
    for(int i=first;i>=0 && i<=last;i++)changed|=add_one(i,amount);
    if(changed && (id!=ACH_WALL || wall_before/30!=achievement_progress[ACH_WALL_60]/30))persist();
}
int achievement_next_unlock(void) {
    for(int i=0;i<ACH_COUNT;i++)if(pending&(1u<<i)) {pending&=~(1u<<i);return i;}
    return -1;
}
