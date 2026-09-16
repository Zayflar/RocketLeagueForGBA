"""Run two copies of the real link protocol over a delayed simulated serial bus."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parents[1]
header=r'''#pragma once
#include <stdint.h>
#include <stdatomic.h>
typedef uint16_t u16;
#define SIOM_ERROR 64
#define SIOM_ENABLE 128
#define SIOM_CONNECTED 8
#define SIOM_SLAVE 4
#define SIOM_ID_MASK 48
#define SIOM_ID_SHIFT 4
#define SIO_MODE_MULTI 8192
#define SIOM_115200 3
#define SIO_IRQ 16384
#define II_SERIAL 7
#define ISR_DEF 0
extern _Atomic u16 regs[2][9];
_Atomic u16 *serial_status(int node);
u16 clock_tick(int node);
void set_irq(int node,void (*fn)(void));
void disable_irq(int node);
#define REG_SIOCNT (*serial_status(NODE))
#define REG_RCNT regs[NODE][1]
#define REG_SIOMLT_SEND regs[NODE][2]
#define REG_SIOMULTI0 regs[NODE][3]
#define REG_SIOMULTI1 regs[NODE][4]
#define REG_IME regs[NODE][5]
#define REG_TM0D clock_tick(NODE)
#define irq_set(id,fn,opts) set_irq(NODE,fn)
#define irq_enable(id) ((void)0)
#define irq_disable(id) disable_irq(NODE)
'''
harness=r'''#define NODE 0
#include "tonc.h"
#include <pthread.h>
#include <assert.h>
#include <stdio.h>
#include <sched.h>
_Atomic u16 regs[2][9];
static _Atomic int connected=1,pending[2];
static void (*handlers[2])(void);
static pthread_mutex_t bus=PTHREAD_MUTEX_INITIALIZER;
static pthread_barrier_t start;
static unsigned ticks[2],transfers,interrupts[2];
_Atomic u16 *serial_status(int n) {
    atomic_fetch_or(&regs[n][0],(connected?8:0)|(n?20:0));
    if(!connected)atomic_fetch_and(&regs[n][0],(u16)~8);
    return &regs[n][0];
}
void set_irq(int n,void (*fn)(void)){handlers[n]=fn;regs[n][5]=1;}
void disable_irq(int n){handlers[n]=0;}
u16 clock_tick(int n) {
    pthread_mutex_lock(&bus);
    /* Artificial latency: not every poll completes a pending transfer. */
    if((regs[0][0]&128) && connected && (++transfers%5)==0) {
        u16 a=regs[0][2],b=regs[1][2];
        if((transfers/5)%13==0)a^=0x2000; /* damaged packet header */
        for(int i=0;i<2;i++){regs[i][3]=a;regs[i][4]=b;pending[i]=1;}
        atomic_fetch_and(&regs[0][0],(u16)~128);
    }
    pthread_mutex_unlock(&bus);
    if(regs[n][5] && atomic_exchange(&pending[n],0) && handlers[n]) {
        if(++interrupts[n]%7)handlers[n](); /* deliberately lose a completion */
    }
    if((++ticks[n]&31)==0)sched_yield();
    return (u16)ticks[n];
}
void host_open(void);void guest_open(void);void host_close(void);void guest_close(void);
int host_exchange(u16,u16*);int guest_exchange(u16,u16*);
int host_step(u16,int,u16*,int*);int guest_step(u16,int,u16*,int*);
static u16 input(int n,int frame){return (frame*37+n*113)&1023;}
static void *run(void *arg) {
    int n=(int)(intptr_t)arg;u16 values[2];
    if(n)guest_open();else host_open();
    pthread_barrier_wait(&start);
    int attempts=0;
    while(!(n?guest_exchange(256,values):host_exchange(256,values))){if(++attempts==10000)fprintf(stderr,"prime node %d sio %x %x send %x %x rx %x %x transfers %u\n",n,regs[0][0],regs[1][0],regs[0][2],regs[1][2],regs[n][3],regs[n][4],transfers);assert(attempts<10000);}
    assert(values[0]==256 && values[1]==256);
    pthread_barrier_wait(&start);
    for(int frame=0;frame<128;frame++) {
        int elapsed=0;attempts=0;
        while(!(n?guest_step(input(n,frame),9,values,&elapsed):host_step(input(n,frame),1+frame%4,values,&elapsed)))
            {if(++attempts==10000)fprintf(stderr,"node %d sio %x %x send %x %x rx %x %x transfers %u\n",n,regs[0][0],regs[1][0],regs[0][2],regs[1][2],regs[n][3],regs[n][4],transfers);assert(attempts<10000);}
        assert(values[0]==input(0,frame) && values[1]==input(1,frame));
        assert(elapsed==1+frame%4);
        if(n && frame%3==0)for(int j=0;j<100;j++)sched_yield();
    }
    return 0;
}
int main(void) {
    pthread_t a,b;pthread_barrier_init(&start,0,2);
    pthread_create(&a,0,run,(void*)0);pthread_create(&b,0,run,(void*)1);
    pthread_join(a,0);pthread_join(b,0);
    connected=0;u16 values[2];assert(!host_exchange(0,values));
    host_close();guest_close();
    puts("PASS: two peers, delayed/lost/corrupt packets, sequence wrap, identical inputs/timing, disconnect");
}
'''
with tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp);(p/'tonc.h').write_text(header);(p/'test.c').write_text(harness)
    objects=[]
    for n,name in enumerate(('host','guest')):
        obj=p/(name+'.o');objects.append(str(obj))
        flags=[f'-Dlink_{fn}={name}_{fn}' for fn in ('open','close','player_id','exchange','step')]
        subprocess.run(['cc','-std=gnu11','-O1','-fsanitize=undefined',f'-DNODE={n}',*flags,'-I',tmp,'-I',str(root),'-c',str(root/'link.c'),'-o',str(obj)],check=True)
    subprocess.run(['cc','-std=gnu11','-O1','-fsanitize=undefined','-I',tmp,str(p/'test.c'),*objects,'-pthread','-o',str(p/'test')],check=True)
    subprocess.run([str(p/'test')],check=True,timeout=30)
