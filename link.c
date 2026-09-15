#include "link.h"

/* Two-console deterministic input exchange over the GBA multiplayer port.
   Serial IRQ captures packets even while the peer is rendering a frame. */
static volatile u16 received[2];
static volatile unsigned expected,ready;
static unsigned pending,phase,have_last;
static u16 pending_packet,last_packet;
static u16 step_buttons[2];

static void link_receive(void) {
    if(REG_SIOCNT&SIOM_ERROR)return;
    u16 a=REG_SIOMULTI0,b=REG_SIOMULTI1;
    if((a&0xe000)!=0x8000 || (b&0xe000)!=0x8000)return;
    if(((a>>10)&7)!=expected || ((b>>10)&7)!=expected)return;
    received[0]=a&1023;received[1]=b&1023;
    ready=1;
}
void link_open(void) {
    expected=ready=pending=phase=have_last=0;
    REG_RCNT=0;
    REG_SIOCNT=SIO_MODE_MULTI|SIOM_115200|SIO_IRQ;
    REG_SIOMLT_SEND=0x8100;
    irq_set(II_SERIAL,link_receive,ISR_DEF);
    irq_enable(II_SERIAL);
}
void link_close(void) {
    irq_disable(II_SERIAL);
    REG_SIOCNT=0;REG_RCNT=0;
    expected=ready=pending=phase=have_last=0;
}
int link_player_id(void) {return (REG_SIOCNT&SIOM_ID_MASK)>>SIOM_ID_SHIFT;}
int link_exchange(u16 payload,u16 values[2]) {
    if(!pending) {
        pending_packet=0x8000|(expected<<10)|(payload&1023);
        REG_SIOMLT_SEND=pending_packet;
        pending=1;
    }
    u16 started=REG_TM0D;
    while(!ready) {
        u16 status=REG_SIOCNT;
        if(!(status&SIOM_CONNECTED) || link_player_id()>1)return 0;
        if(!(status&SIOM_SLAVE) && !(status&SIOM_ENABLE)) {
            u16 peer=REG_SIOMULTI1;
            /* Re-send the previous generation until the peer advances. This
               also recovers a delayed serial IRQ during a VRAM DMA copy. */
            int behind=have_last && (peer&0xe000)==0x8000 &&
                ((peer>>10)&7)==((expected+7)&7);
            REG_SIOMLT_SEND=behind?last_packet:pending_packet;
            REG_SIOCNT=SIO_MODE_MULTI|SIOM_115200|SIO_IRQ|SIOM_ENABLE;
        }
        /* Return to the UI after 100 ms; retain this exact pending input. */
        if((u16)(REG_TM0D-started)>1638)return 0;
    }
    /* Exclude the serial ISR while advancing the packet generation. */
    u16 ime=REG_IME;REG_IME=0;
    values[0]=received[0];values[1]=received[1];
    last_packet=pending_packet;have_last=1;
    ready=0;expected=(expected+1)&7;pending=0;
    REG_IME=ime;
    return 1;
}
int link_step(u16 buttons,int elapsed,u16 buttons_out[2],int *elapsed_out) {
    if(!phase) {
        if(!link_exchange(buttons,step_buttons))return 0;
        phase=1;
    }
    u16 timing[2];
    if(elapsed<1)elapsed=1;
    if(elapsed>15)elapsed=15;
    if(!link_exchange(link_player_id()==0?elapsed:0,timing))return 0;
    buttons_out[0]=step_buttons[0];buttons_out[1]=step_buttons[1];
    *elapsed_out=timing[0]>0 && timing[0]<=15?timing[0]:1;
    phase=0;
    return 1;
}
